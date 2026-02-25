#![allow(unused_imports)]
use lazy_static::lazy_static;
use std::collections::HashMap;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::time::{Duration, Instant};

use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Request, Response, StatusCode};
use hyper_util::rt::TokioIo;
use opentelemetry::KeyValue;
use opentelemetry::global::{self, BoxedSpan, BoxedTracer};
use opentelemetry::metrics::{Histogram, UpDownCounter};
use opentelemetry::trace::{Span, SpanKind, Status, Tracer};
use opentelemetry_otlp::{
    SpanExporter as OtlpSpanExporter, WithExportConfig, WithHttpConfig, WithTonicConfig,
};
use opentelemetry_sdk::metrics::{PeriodicReader, SdkMeterProvider};
use opentelemetry_sdk::runtime::Tokio;
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_semantic_conventions::attribute::{
    HTTP_REQUEST_METHOD, HTTP_RESPONSE_STATUS_CODE, URL_PATH,
};
use opentelemetry_semantic_conventions::metric::{
    HTTP_SERVER_ACTIVE_REQUESTS, HTTP_SERVER_REQUEST_DURATION,
};
use opentelemetry_stdout;
use serde;
use tokio::net::TcpListener;

fn fibonacci(n: u8) -> u16 {
    match n {
        0 | 1 => n as u16,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

async fn index(
    r: Request<hyper::body::Incoming>,
    span: &mut BoxedSpan,
) -> Result<Response<Full<Bytes>>, Infallible> {
    println!("{} {}\nHeaders:\n{:#?}", r.method(), r.uri(), r.headers());
    span.set_attribute(KeyValue::new(
        HTTP_RESPONSE_STATUS_CODE,
        StatusCode::OK.as_u16() as i64,
    ));
    Ok(Response::new(Full::new(Bytes::from("Hello, World!"))))
}

// this struct makes it convenient to validate numbers exceeding the u8 limit
#[derive(Debug, serde::Deserialize)]
struct FibonacciRequest {
    number: u8,
}

async fn calculate_fibonacci(
    r: Request<hyper::body::Incoming>,
    span: &mut BoxedSpan,
) -> Result<Response<Full<Bytes>>, Infallible> {
    // parse the input body data into Bytes format
    let body = r.into_body().collect().await.unwrap();
    let body_byte_stream = body.to_bytes();

    // deserialize the json body into FibonacciRequest struct
    // returning an apt error if the number is too large, to keep server responsive
    let body_data = match serde_json::from_slice::<FibonacciRequest>(&body_byte_stream) {
        Ok(data) => data,
        Err(err) => {
            let error_message = err.to_string();

            let error_payload = serde_json::json!({
                "error": error_message
            });
            span.set_status(Status::Error {
                description: error_message.into(),
            });
            span.set_attribute(KeyValue::new(
                HTTP_RESPONSE_STATUS_CODE,
                StatusCode::UNPROCESSABLE_ENTITY.as_u16() as i64,
            ));

            return Ok(Response::builder()
                .status(StatusCode::UNPROCESSABLE_ENTITY)
                .header("Content-Type", "application/json")
                .body(Full::new(Bytes::from(error_payload.to_string())))
                .unwrap());
        }
    };

    // sleep for random amount of time to add variance and emulate "real work"
    let sleep_time = rand::random_range(250..750);
    tokio::time::sleep(Duration::from_millis(sleep_time)).await;

    let number = body_data.number;
    let fib = fibonacci(number);

    // define and set relevant information as the span attributes for more context
    // using ::new for instantiating KeyValue struct as it's marked as non-exhaustive
    let number_key_value = KeyValue::new("fibonacci.number", number as i64);
    let fib_key_value = KeyValue::new("fibonacci.result", fib as i64);

    span.set_attributes(vec![number_key_value, fib_key_value]);
    span.set_attribute(KeyValue::new(
        HTTP_RESPONSE_STATUS_CODE,
        StatusCode::OK.as_u16() as i64,
    ));

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

// handles routing incoming requests to appropriate request handler functions
async fn router(
    request: Request<hyper::body::Incoming>,
) -> Result<Response<Full<Bytes>>, Infallible> {
    // convert to owned Strings before request is moved into the handler below
    let path = request.uri().path().to_string();
    let method = request.method().to_string();

    println!("router: received request for {}", path);

    let method_kv = KeyValue::new(HTTP_REQUEST_METHOD, method.clone());
    let path_kv = KeyValue::new(URL_PATH, path.clone());

    let mut span = TRACER
        .span_builder(format!("{} {}", method, path))
        .with_kind(SpanKind::Server)
        .with_attributes(vec![method_kv.clone(), path_kv.clone()])
        .start(&*TRACER);

    // active_requests labels only use method+path: we don't know status_code yet
    let inflight_attrs = [method_kv.clone(), path_kv.clone()];

    // increment before the handler runs to track true in-flight requests
    METRICS.active_requests.add(1, &inflight_attrs);

    // start the timer before dispatching to measure end-to-end request duration
    let start = Instant::now();

    let result = match path.as_str() {
        "/" => index(request, &mut span).await,
        "/fibonacci" => calculate_fibonacci(request, &mut span).await,
        _ => {
            let sleep_time = rand::random_range(50..100);
            tokio::time::sleep(Duration::from_millis(sleep_time)).await;
            span.set_status(Status::Error {
                description: "Resource not found".into(),
            });
            span.set_attribute(KeyValue::new(
                HTTP_RESPONSE_STATUS_CODE,
                StatusCode::NOT_FOUND.as_u16() as i64,
            ));
            Ok(Response::builder()
                .status(StatusCode::NOT_FOUND)
                .body(Full::new(Bytes::from("Resource not found")))
                .unwrap())
        }
    };

    // decrement now that the request has completed
    METRICS.active_requests.add(-1, &inflight_attrs);

    // record request duration and total count with the full attribute set including status
    let status_code = result.as_ref().unwrap().status().as_u16() as i64;
    // OTel semantic convention: http.server.request.duration must be in seconds
    let duration_secs = start.elapsed().as_secs_f64();

    let completed_attrs = [
        method_kv,
        path_kv,
        KeyValue::new(HTTP_RESPONSE_STATUS_CODE, status_code),
    ];
    METRICS
        .request_duration
        .record(duration_secs, &completed_attrs);

    result
}

// initialize global variables to keep duplication to a minimum
lazy_static! {
    static ref SIGNOZ_HEADERS: HashMap<String, String> = {
        let mut headers = HashMap::new();
        if let Ok(key) = std::env::var("SIGNOZ_INGESTION_KEY") {
            headers.insert("signoz-ingestion-key".to_string(), key);
        }
        headers
    };
    static ref OTLP_ENDPOINT: String =
        std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").unwrap_or_default();
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
                // OTel-recommended boundaries for HTTP latency (in seconds).
                // Without these, all sub-second requests collapse into a single default [0, 5) bucket,
                // making P95/P99 meaningless.
                .with_boundaries(vec![
                    0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5,
                    10.0,
                ])
                .build(),
        }
    };
    static ref TRACER: BoxedTracer = global::tracer("opentelemetry-rust-demo");
}

fn init_tracer_provider() {
    // * feel free to use the gRPC exporter if using a local collector instance
    // let otlp_exporter = OtlpSpanExporter::builder()
    //     .with_tonic()
    //     .build()
    //     .unwrap();

    // * use the HTTP exporter when targeting a cloud backend or a collector behind a proxy
    let otlp_endpoint = format!("{}/v1/traces", *OTLP_ENDPOINT);
    let otlp_exporter = OtlpSpanExporter::builder()
        .with_http()
        .with_protocol(opentelemetry_otlp::Protocol::HttpBinary)
        .with_endpoint(otlp_endpoint)
        .with_headers(SIGNOZ_HEADERS.clone())
        .build()
        .unwrap();

    let provider = SdkTracerProvider::builder()
        .with_simple_exporter(opentelemetry_stdout::SpanExporter::default())
        .with_batch_exporter(otlp_exporter)
        .build();

    global::set_tracer_provider(provider);
}

fn init_meter_provider() {
    let otlp_endpoint = format!("{}/v1/metrics", *OTLP_ENDPOINT);

    let otlp_exporter = opentelemetry_otlp::MetricExporter::builder()
        .with_http()
        .with_endpoint(otlp_endpoint)
        .with_headers(SIGNOZ_HEADERS.clone())
        .with_protocol(opentelemetry_otlp::Protocol::HttpBinary)
        .build()
        .expect("Failed to create OTLP exporter");

    // the reader object controls how often metrics are exported
    let stdout_reader = PeriodicReader::builder(opentelemetry_stdout::MetricExporter::default())
        .with_interval(Duration::from_secs(5))
        .build();
    let otlp_reader = PeriodicReader::builder(otlp_exporter)
        // this should be high enough to avoid overloading the backend but low enough for accurate analysis
        .with_interval(Duration::from_secs(30))
        .build();

    let provider = SdkMeterProvider::builder()
        .with_reader(otlp_reader)
        .with_reader(stdout_reader)
        .build();

    global::set_meter_provider(provider);
}

// holds initialized metric instruments — created once and reused across all requests
struct AppMetrics {
    // tracks currently in-flight requests (incremented on arrival, decremented on completion)
    active_requests: UpDownCounter<i64>,
    // measures end-to-end HTTP request duration in milliseconds as a histogram
    // this powers latency percentile dashboards (p50, p95, p99) in your backend
    request_duration: Histogram<f64>,
}

#[tokio::main]
async fn main() {
    let addr = SocketAddr::from(([127, 0, 0, 1], 8085));
    let listener = TcpListener::bind(&addr).await.unwrap();

    println!("Listening on http://{}", addr);
    init_tracer_provider();
    init_meter_provider();

    loop {
        let (stream, _) = listener.accept().await.unwrap();

        // Use an adapter to access something implementing `tokio::io` traits as if they implement
        // `hyper::rt` IO traits.
        let io = TokioIo::new(stream);

        // Spawn a tokio task to serve multiple connections concurrently
        tokio::spawn(async move {
            if let Err(err) = http1::Builder::new()
                .serve_connection(io, service_fn(router))
                .await
            {
                eprintln!("Error serving connection {:?}", err);
            }
        });
    }
}
