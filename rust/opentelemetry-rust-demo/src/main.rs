#![allow(unused_imports)]
use std::collections::HashMap;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::sync::OnceLock;

use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Request, Response, StatusCode};
use hyper_util::rt::TokioIo;
use opentelemetry::KeyValue;
use opentelemetry::global::{self, BoxedSpan, BoxedTracer};
use opentelemetry::trace::{Span, SpanKind, Status, Tracer};
use opentelemetry_otlp::{
    SpanExporter as OtlpSpanExporter, WithExportConfig, WithHttpConfig, WithTonicConfig,
};
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_semantic_conventions::attribute::{
    HTTP_REQUEST_METHOD, HTTP_RESPONSE_STATUS_CODE, URL_PATH,
};
use opentelemetry_stdout::SpanExporter as StdoutSpanExporter;
use serde;
use tokio::net::TcpListener;

fn fibonacci(n: u8) -> u16 {
    match n {
        0 | 1 => n as u16,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

async fn index(r: Request<hyper::body::Incoming>) -> Result<Response<Full<Bytes>>, Infallible> {
    println!("{} {}\nHeaders:\n{:#?}", r.method(), r.uri(), r.headers());
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
    let tracer = get_tracer();
    let path = request.uri().path();
    println!("router: received request for {}", path);

    let mut span = tracer
        .span_builder(format!("{} {}", request.method(), path))
        .with_kind(SpanKind::Server)
        .with_attributes(vec![
            KeyValue::new(HTTP_REQUEST_METHOD, request.method().to_string()),
            KeyValue::new(URL_PATH, path.to_string()),
        ])
        .start(tracer);

    match path {
        "/" => index(request).await,
        "/fibonacci" => calculate_fibonacci(request, &mut span).await,
        _ => {
            // explicitly set the status as error for better visibility in the trace
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
    }
}

fn init_tracer_provider() {
    let headers = HashMap::from([(
        "signoz-ingestion-key".to_string(),
        std::env::var("SIGNOZ_INGESTION_KEY").unwrap(),
    )]);

    // * feel free to use the gRPC exporter if using a local collector instance
    // let otlp_exporter = OtlpSpanExporter::builder()
    //     .with_tonic()
    //     .build()
    //     .unwrap();

    // * use the HTTP exporter if using a cloud-based backend like Signoz or a collector running behind a proxy
    let otlp_endpoint = std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").unwrap() + "/v1/traces";
    let otlp_exporter = OtlpSpanExporter::builder()
        .with_http()
        .with_protocol(opentelemetry_otlp::Protocol::HttpJson)
        .with_endpoint(otlp_endpoint)
        .with_headers(headers)
        .build()
        .unwrap();

    let provider = SdkTracerProvider::builder()
        // use simple exporter for debugging on the terminal
        .with_simple_exporter(StdoutSpanExporter::default())
        // use batch exporter to reduce network round trips
        .with_batch_exporter(otlp_exporter)
        .build();

    global::set_tracer_provider(provider);
}

// ensures the tracer is initialized only once throughout the application's lifespan
fn get_tracer() -> &'static BoxedTracer {
    static TRACER: OnceLock<BoxedTracer> = OnceLock::new();
    TRACER.get_or_init(|| global::tracer("opentelemetry-rust-demo"))
}

#[tokio::main]
async fn main() {
    let addr = SocketAddr::from(([127, 0, 0, 1], 8085));
    let listener = TcpListener::bind(&addr).await.unwrap();

    println!("Listening on http://{}", addr);
    init_tracer_provider();

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
