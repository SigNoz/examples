use std::collections::HashMap;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::sync::OnceLock;
use std::time::{Duration, Instant};

use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Request, Response, StatusCode};
use hyper_util::rt::TokioIo;
use lazy_static::lazy_static;
use opentelemetry::KeyValue;
use opentelemetry::global;
use opentelemetry::metrics::{Histogram, UpDownCounter};
use opentelemetry::propagation::{Extractor, Injector};
use opentelemetry::trace::{Status, TracerProvider as _};
use opentelemetry_appender_tracing::layer::OpenTelemetryTracingBridge;
use opentelemetry_otlp::{
    LogExporter as OtlpLogExporter, SpanExporter as OtlpSpanExporter, WithExportConfig,
    WithTonicConfig,
};
use opentelemetry_sdk::logs::{BatchLogProcessor, SdkLoggerProvider, SimpleLogProcessor};
use opentelemetry_sdk::metrics::{PeriodicReader, SdkMeterProvider};
use opentelemetry_sdk::propagation::TraceContextPropagator;
use opentelemetry_sdk::trace::{SdkTracer, SdkTracerProvider};
use opentelemetry_semantic_conventions::attribute::{
    HTTP_REQUEST_METHOD, HTTP_RESPONSE_STATUS_CODE, URL_PATH,
};
use opentelemetry_semantic_conventions::metric::{
    HTTP_SERVER_ACTIVE_REQUESTS, HTTP_SERVER_REQUEST_DURATION,
};
use opentelemetry_stdout;
use tokio::net::TcpListener;
use tonic::metadata::{MetadataMap, MetadataValue};
use tonic::transport::ClientTlsConfig;
use tracing::{Instrument, Span, debug, error, info, info_span};
use tracing_opentelemetry::OpenTelemetrySpanExt;
use tracing_subscriber::{EnvFilter, prelude::*};

// we maintain an explicit OnceLock for logs because `opentelemetry::global` doesn't expose
// trace/metric-equivalent global logger handlers
static LOGGER_PROVIDER: OnceLock<SdkLoggerProvider> = OnceLock::new();

// adapts Hyper headers to OTel propagation so we can extract `traceparent` from inbound requests
struct HeaderExtractor<'a>(&'a hyper::header::HeaderMap);

impl<'a> Extractor for HeaderExtractor<'a> {
    fn get(&self, key: &str) -> Option<&str> {
        self.0.get(key).and_then(|value| value.to_str().ok())
    }

    fn keys(&self) -> Vec<&str> {
        self.0.keys().map(|k| k.as_str()).collect()
    }
}

struct HeaderInjector<'a>(&'a mut hyper::header::HeaderMap);

impl<'a> Injector for HeaderInjector<'a> {
    fn set(&mut self, key: &str, value: String) {
        let header_name = match hyper::header::HeaderName::from_bytes(key.as_bytes()) {
            Ok(name) => name,
            Err(_) => return,
        };
        let header_value = match hyper::header::HeaderValue::from_str(&value) {
            Ok(value) => value,
            Err(_) => return,
        };
        self.0.insert(header_name, header_value);
    }
}

struct AppMetrics {
    // tracks currently in-flight requests
    active_requests: UpDownCounter<i64>,
    // captures end-to-end HTTP request latency (seconds)
    request_duration: Histogram<f64>,
}

// initialize global variables to keep duplication to a minimum
// these will be initialized when called, and reused thereafter throughout the application, guaranteeing that
// metrics and tracer objects initialize AFTER the corresponding pipelines have been setup
lazy_static! {
    static ref SIGNOZ_HEADERS: HashMap<String, String> = {
        let mut headers = HashMap::new();
        if let Ok(key) = std::env::var("SIGNOZ_INGESTION_KEY") {
            headers.insert("signoz-ingestion-key".to_string(), key);
        } else {
            panic!("SIGNOZ_INGESTION_KEY not set");
        }
        headers
    };
    static ref OTLP_ENDPOINT: String =
        std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").expect("OTEL_EXPORTER_OTLP_ENDPOINT not set");

    // we don't need a global meter handle later because we'll reuse instruments directly
    static ref METRICS: AppMetrics = {
        let meter = global::meter("opentelemetry-rust-demo");
        AppMetrics {
            active_requests: meter
                .i64_up_down_counter(HTTP_SERVER_ACTIVE_REQUESTS)
                .with_description("Active HTTP requests")
                .with_unit("{request}")
                .build(),
            request_duration: meter
                .f64_histogram(HTTP_SERVER_REQUEST_DURATION)
                .with_description("End-to-end HTTP request duration in seconds")
                .with_unit("s")
                // OTel-recommended boundaries for HTTP latency (in seconds)
                // Without these, all sub-second requests collapse into a single default [0, 5) bucket,
                // making P95/P99 meaningless
                .with_boundaries(vec![
                    0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0,
                ])
                .build(),
        }
    };
}

fn signoz_tonic_metadata() -> MetadataMap {
    let mut metadata = MetadataMap::new();
    if let Some(ingestion_key) = SIGNOZ_HEADERS.get("signoz-ingestion-key") {
        if let Ok(metadata_value) = MetadataValue::try_from(ingestion_key.as_str()) {
            metadata.insert("signoz-ingestion-key", metadata_value);
        }
    }
    metadata
}

fn fibonacci(n: u8) -> u128 {
    match n {
        0 | 1 => n as u128,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

async fn index(_: Request<hyper::body::Incoming>) -> Result<Response<Full<Bytes>>, Infallible> {
    Span::current().set_attribute(HTTP_RESPONSE_STATUS_CODE, StatusCode::OK.as_u16() as i64);
    Ok(Response::new(Full::new(Bytes::from("Hello, World!"))))
}

// this struct makes it convenient to validate numbers exceeding the u8 limit
#[derive(Debug, serde::Deserialize)]
struct FibonacciRequest {
    number: u8,
}

async fn calculate_fibonacci(
    request: Request<hyper::body::Incoming>,
) -> Result<Response<Full<Bytes>>, Infallible> {
    let body = request.into_body().collect().await.unwrap();
    let body_byte_stream = body.to_bytes();

    let body_data = match serde_json::from_slice::<FibonacciRequest>(&body_byte_stream) {
        Ok(data) => data,
        Err(err) => {
            let error_message = err.to_string();
            let error_payload = serde_json::json!({ "error": error_message });

            Span::current().set_status(Status::error(error_message.clone()));
            Span::current().set_attribute(
                HTTP_RESPONSE_STATUS_CODE,
                StatusCode::UNPROCESSABLE_ENTITY.as_u16() as i64,
            );
            Span::current().set_attribute("error.type", "Invalid Input");
            Span::current().set_attribute("error.message", error_message.clone());

            error!(
                error.message = %error_message,
                error.type = "Invalid Input",
                "error parsing fibonacci payload"
            );
            return Ok(Response::builder()
                .status(StatusCode::UNPROCESSABLE_ENTITY)
                .header("Content-Type", "application/json")
                .body(Full::new(Bytes::from(error_payload.to_string())))
                .unwrap());
        }
    };

    tokio::time::sleep(Duration::from_millis(rand::random_range(250..750))).await;

    let number = body_data.number;
    let fib = fibonacci(number);

    Span::current().set_attribute("fibonacci.number", number as i64);
    Span::current().set_attribute("fibonacci.result", fib as i64);
    Span::current().set_attribute(HTTP_RESPONSE_STATUS_CODE, StatusCode::OK.as_u16() as i64);

    Ok(Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "application/json")
        .body(Full::new(Bytes::from(
            serde_json::json!({
                "number": number,
                "result": fib
            })
            .to_string(),
        )))
        .unwrap())
}

async fn httpbin(_: Request<hyper::body::Incoming>) -> Result<Response<Full<Bytes>>, Infallible> {
    // create a client span as child of the current request span
    let client_span = info_span!(
        "http.client",
        otel.name = "GET https://httpbin.org/anything",
        otel.kind = "client",
        http.request.method = "GET",
        url.full = "https://httpbin.org/anything"
    );

    async move {
        let mut outbound_headers = hyper::header::HeaderMap::new();
        global::get_text_map_propagator(|prop| {
            // inject current span context so downstream services can join this trace
            prop.inject_context(
                &Span::current().context(),
                &mut HeaderInjector(&mut outbound_headers),
            );
        });

        let traceparent = outbound_headers
            .get("traceparent")
            .and_then(|v| v.to_str().ok())
            .map(str::to_string);

        let client = reqwest::Client::new();
        let upstream = client
            .get("https://httpbin.org/anything")
            .headers(outbound_headers.clone())
            .send()
            .await;

        match upstream {
            Ok(resp) => {
                let upstream_status = resp.status();
                let upstream_body = resp.text().await.unwrap_or_default();
                let upstream_json = serde_json::from_str::<serde_json::Value>(&upstream_body)
                    .unwrap_or_else(|_| serde_json::json!({ "raw": upstream_body }));

                Span::current()
                    .set_attribute(HTTP_RESPONSE_STATUS_CODE, upstream_status.as_u16() as i64);
                info!(
                    http.response.status_code = upstream_status.as_u16(),
                    "httpbin request succeeded"
                );

                Ok(Response::builder()
                    .status(StatusCode::OK)
                    .header("Content-Type", "application/json")
                    .body(Full::new(Bytes::from(
                        serde_json::json!({
                            "note": "This endpoint calls https://httpbin.org/anything with propagated trace context.",
                            "propagated": {
                                "traceparent": traceparent
                            },
                            "httpbin": upstream_json
                        })
                        .to_string(),
                    )))
                    .unwrap())
            }
            Err(err) => {
                let error_message = err.to_string();
                Span::current().set_status(Status::error(error_message.clone()));
                Span::current().set_attribute(
                    HTTP_RESPONSE_STATUS_CODE,
                    StatusCode::SERVICE_UNAVAILABLE.as_u16() as i64,
                );
                error!(error.message = %error_message, "httpbin request failed");

                Ok(Response::builder()
                    .status(StatusCode::SERVICE_UNAVAILABLE)
                    .header("Content-Type", "application/json")
                    .body(Full::new(Bytes::from(
                        serde_json::json!({
                            "error": error_message
                        })
                        .to_string(),
                    )))
                    .unwrap())
            }
        }
    }
    .instrument(client_span)
    .await
}

fn init_tracer_provider() -> SdkTracerProvider {
    // set the propagator to be used for extracting and injecting trace context; extraction and injection won't work
    // unless propagators are defined globally first
    global::set_text_map_propagator(opentelemetry::propagation::TextMapCompositePropagator::new(
        vec![Box::new(TraceContextPropagator::new())],
    ));

    // use gRPC exporter with TLS and metadata headers for SigNoz cloud
    let otlp_endpoint = OTLP_ENDPOINT.clone();
    let otlp_exporter = OtlpSpanExporter::builder()
        .with_tonic()
        .with_protocol(opentelemetry_otlp::Protocol::Grpc)
        .with_endpoint(otlp_endpoint)
        .with_tls_config(ClientTlsConfig::new().with_native_roots())
        .with_metadata(signoz_tonic_metadata())
        .build()
        .unwrap();

    let provider = SdkTracerProvider::builder()
        .with_batch_exporter(otlp_exporter)
        .build();

    global::set_tracer_provider(provider.clone());
    provider
}

fn init_meter_provider() {
    let otlp_endpoint = OTLP_ENDPOINT.clone();

    // the reader object controls how often metrics are exported
    // let stdout_reader = PeriodicReader::builder(opentelemetry_stdout::MetricExporter::default())
    //     .with_interval(Duration::from_secs(5))
    //     .build();

    let otlp_exporter = opentelemetry_otlp::MetricExporter::builder()
        .with_tonic()
        .with_protocol(opentelemetry_otlp::Protocol::Grpc)
        .with_endpoint(otlp_endpoint)
        .with_tls_config(ClientTlsConfig::new().with_native_roots())
        .with_metadata(signoz_tonic_metadata())
        .build()
        .expect("Failed to create OTLP exporter");

    // the interval should be high enough to avoid overloading the backend but low enough for accurate analysis
    let otlp_reader = PeriodicReader::builder(otlp_exporter)
        .with_interval(Duration::from_secs(30))
        .build();

    let provider = SdkMeterProvider::builder()
        // enable stdout reader for debugging
        // .with_reader(stdout_reader)
        .with_reader(otlp_reader)
        .build();
    global::set_meter_provider(provider);
}

fn init_logger_provider() {
    let otlp_endpoint = OTLP_ENDPOINT.clone();
    let otlp_exporter = OtlpLogExporter::builder()
        .with_tonic()
        .with_protocol(opentelemetry_otlp::Protocol::Grpc)
        .with_endpoint(otlp_endpoint)
        .with_tls_config(ClientTlsConfig::new().with_native_roots())
        .with_metadata(signoz_tonic_metadata())
        .build()
        .unwrap();

    let provider = SdkLoggerProvider::builder()
        .with_log_processor(SimpleLogProcessor::new(
            opentelemetry_stdout::LogExporter::default(),
        ))
        .with_log_processor(BatchLogProcessor::builder(otlp_exporter).build())
        .build();

    // store the provider in a OnceLock as there is no global logger setter API equivalent to tracer/meter globals
    let _ = LOGGER_PROVIDER.set(provider);
}

fn init_tracing_subscriber(tracer: SdkTracer) {
    // filter noisy logs from dependencies
    let filter = EnvFilter::new(
        "info,opentelemetry_rust_demo=debug,opentelemetry_sdk=warn,opentelemetry_otlp=warn,opentelemetry_http=warn,reqwest=warn,hyper_util=warn,hyper=warn,h2=warn,tonic=warn",
    );
    let logger_provider = LOGGER_PROVIDER
        .get()
        .expect("logger provider should be initialized before tracing subscriber");
    // bridge tracing events -> OTel logs
    let otel_log_layer = OpenTelemetryTracingBridge::new(logger_provider);
    // bridge tracing spans -> OTel traces
    let otel_span_layer = tracing_opentelemetry::layer().with_tracer(tracer);

    tracing_subscriber::registry()
        .with(filter)
        .with(tracing_subscriber::fmt::layer())
        .with(otel_span_layer)
        .with(otel_log_layer)
        .init();
}

async fn router(
    request: Request<hyper::body::Incoming>,
) -> Result<Response<Full<Bytes>>, Infallible> {
    // convert to owned Strings before request is moved into handlers below
    let path = request.uri().path().to_string();
    let method = request.method().to_string();

    // extract incoming parent context from HTTP headers;
    // start extraction from a fresh root context to avoid accidental inheritance
    let parent_cx = global::get_text_map_propagator(|prop| {
        prop.extract_with_context(
            &opentelemetry::Context::new(),
            &HeaderExtractor(request.headers()),
        )
    });
    let span_name = format!("{} {}", method, path);
    // use stable local tracing span name, and override exported OTel span name via `otel.name`
    let request_span = info_span!(
        "http.server",
        otel.name = %span_name,
        otel.kind = "server",
        http.method = %method,
        url.path = %path
    );
    let _ = request_span.set_parent(parent_cx);

    // instrumenting the async block keeps span context active across all await points
    async move {
        debug!("received request");

        Span::current().set_attribute(HTTP_REQUEST_METHOD, method.clone());
        Span::current().set_attribute(URL_PATH, path.clone());

        let method_kv = KeyValue::new(HTTP_REQUEST_METHOD, method.clone());
        let path_kv = KeyValue::new(URL_PATH, path.clone());
        // active_requests labels only use method+path because status is unknown at start
        let inflight_attrs = [method_kv.clone(), path_kv.clone()];

        // increment before handler runs to capture true in-flight requests
        METRICS.active_requests.add(1, &inflight_attrs);
        let start = Instant::now();

        let result = match path.as_str() {
            "/" => index(request).await,
            "/fibonacci" => calculate_fibonacci(request).await,
            "/external" => httpbin(request).await,
            _ => {
                tokio::time::sleep(Duration::from_millis(rand::random_range(50..100))).await;
                Span::current().set_status(Status::error("Resource not found"));
                Span::current().set_attribute(
                    HTTP_RESPONSE_STATUS_CODE,
                    StatusCode::NOT_FOUND.as_u16() as i64,
                );
                Span::current().set_attribute(URL_PATH, path.clone());
                Span::current().set_attribute(HTTP_REQUEST_METHOD, method.clone());
                error!("resource not found");

                Ok(Response::builder()
                    .status(StatusCode::NOT_FOUND)
                    .body(Full::new(Bytes::from("Resource not found")))
                    .unwrap())
            }
        };

        // decrement now that request handling is complete
        METRICS.active_requests.add(-1, &inflight_attrs);

        // record end-to-end request duration and final status
        let status_code = result.as_ref().unwrap().status().as_u16() as i64;
        let duration_secs = start.elapsed().as_secs_f64();
        let completed_attrs = [
            method_kv,
            path_kv,
            KeyValue::new(HTTP_RESPONSE_STATUS_CODE, status_code),
        ];
        METRICS
            .request_duration
            .record(duration_secs, &completed_attrs);

        Span::current().set_attribute(HTTP_RESPONSE_STATUS_CODE, status_code);
        if status_code >= 500 {
            Span::current().set_status(Status::error(format!("HTTP {}", status_code)));
        }

        result
    }
    .instrument(request_span)
    .await
}

#[tokio::main]
async fn main() {
    let addr = SocketAddr::from(([127, 0, 0, 1], 8085));
    let listener = TcpListener::bind(&addr).await.unwrap();

    let tracer_provider = init_tracer_provider();
    let tracing_layer_tracer = tracer_provider.tracer("opentelemetry-rust-demo");
    init_logger_provider();
    init_meter_provider();
    init_tracing_subscriber(tracing_layer_tracer);

    info!(server.address = %addr, "OpenTelemetry Rust Demo app: starting up");

    loop {
        let (stream, _) = listener.accept().await.unwrap();
        // adapt tokio IO traits to hyper runtime IO traits
        let io = TokioIo::new(stream);

        // serve each connection concurrently
        tokio::spawn(async move {
            if let Err(err) = http1::Builder::new()
                .serve_connection(io, service_fn(router))
                .await
            {
                error!(error.message = ?err, "error serving connection");
            }
        });
    }
}
