use std::convert::Infallible;
use std::net::SocketAddr;

use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Request, Response, StatusCode};
use hyper_util::rt::TokioIo;
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

#[derive(Debug, serde::Deserialize)]
struct FibonacciRequest {
    number: u8,
}

async fn calculate_fibonacci(
    r: Request<hyper::body::Incoming>,
) -> Result<Response<Full<Bytes>>, Infallible> {
    // parse the input body data into Bytes format
    let body = r.into_body().collect().await.unwrap();
    let body_byte_stream = body.to_bytes();

    // deserialize the json body into FibonacciRequest struct
    // returning an apt error if the number is too large, to keep server responsive
    let fib: u16;
    match serde_json::from_slice::<FibonacciRequest>(&body_byte_stream) {
        Ok(body_data) => {
            fib = fibonacci(body_data.number);
            Ok(Response::new(Full::new(Bytes::from(fib.to_string()))))
        }
        Err(err) => {
            return Ok(Response::builder()
                .status(StatusCode::UNPROCESSABLE_ENTITY)
                .body(Full::new(Bytes::from(format!("Error: {}", err))))
                .unwrap());
        }
    }

    // let Ok(body_data) = serde_json::from_slice::<FibonacciRequest>(&body_byte_stream) else {
    //     return Ok(Response::builder()
    //         .status(StatusCode::UNPROCESSABLE_ENTITY)
    //         .body(Full::new(Bytes::from("Number too large")))
    //         .unwrap());
    // };

    // let fib = fibonacci(body_data.number);
    // Ok(Response::new(Full::new(Bytes::from(fib.to_string()))))
}

/// handles routing incoming requests to appropriate request handler functions
async fn router(
    request: Request<hyper::body::Incoming>,
) -> Result<Response<Full<Bytes>>, Infallible> {
    println!("router: received request for {}", request.uri().path());
    match request.uri().path() {
        "/" => index(request).await,
        "/fibonacci" => calculate_fibonacci(request).await,
        _ => Ok(Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body(Full::new(Bytes::from("Resource not found")))
            .unwrap()),
    }
}

#[tokio::main]
async fn main() {
    let addr = SocketAddr::from(([127, 0, 0, 1], 8085));
    let listener = TcpListener::bind(&addr).await.unwrap();

    println!("Listening on http://{}", addr);

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
