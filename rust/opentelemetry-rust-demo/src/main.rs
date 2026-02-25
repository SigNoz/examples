#![allow(unused_imports)]
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
use opentelemetry_otlp::SpanExporter as OtlpSpanExporter;
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_stdout::SpanExporter;
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
    println!("router: received request for {}", request.uri().path());

    let mut span = tracer
        .span_builder(format!("{} {}", request.method(), request.uri().path()))
        .with_kind(SpanKind::Server)
        .start(tracer);

    match request.uri().path() {
        "/" => index(request).await,
        "/fibonacci" => calculate_fibonacci(request, &mut span).await,
        _ => {
            // explicitly set the status as error for better visibility in the trace
            span.set_status(Status::Error {
                description: "Resource not found".into(),
            });
            Ok(Response::builder()
                .status(StatusCode::NOT_FOUND)
                .body(Full::new(Bytes::from("Resource not found")))
                .unwrap())
        }
    }
}

fn init_tracer_provider() {
    let provider = SdkTracerProvider::builder()
        .with_batch_exporter(SpanExporter::default())
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
