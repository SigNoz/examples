# OpenTelemetry Spring Boot Demo

Demonstrates OpenTelemetry instrumentation for a Spring Boot 3.5 application using:
- **OTel Java Agent** for zero-code auto-instrumentation (HTTP server spans, outbound HTTP client spans with W3C trace context propagation, log correlation)
- **`@WithSpan` + `@SpanAttribute`** for business-logic span enrichment (fibonacci computation)
- **OTel API** (`GlobalOpenTelemetry`) for custom metric implementation

## Stack

- Runtime: Java 21
- Framework: Spring Boot 3.5.x + Spring MVC (Tomcat)
- OTel Agent: `opentelemetry-javaagent` 2.26.0
- OTel API: `opentelemetry-api` 1.47.0
- Annotations: `opentelemetry-instrumentation-annotations` 2.26.0
- Build: Maven

## Prerequisites

- Java 21+
- Maven 3.9+
- A SigNoz Cloud account (or any OTLP-compatible backend)

## Get your SigNoz values

You need two values from SigNoz Cloud:

- **Ingestion key**: from your SigNoz Cloud ingestion keys page
- **Region endpoint**: from your SigNoz Cloud region docs

Use them in this format:

- Endpoint: `https://ingest.<region>.signoz.cloud:443`
- Key: your ingestion key string

## Run it

```bash
# 1. Download the OTel Java Agent JAR (only needed once)
make download-agent

# 2. Start the app
# The Makefile enables experimental HTTP client/server telemetry on the Java agent,
# including http.server.active_requests.
OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.<region>.signoz.cloud:443" \
SIGNOZ_INGESTION_KEY="<your-key>" \
make run
```

The server starts on `http://localhost:8085`.

### Generate load

In a separate terminal:

```bash
chmod +x scripts/load_gen.sh
./scripts/load_gen.sh
```

This continuously generates traffic against `/`, `/invalid`, and `/fibonacci`, using a mix of valid Fibonacci inputs plus occasional invalid values to trigger `422` responses and error spans.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Returns "Hello, World!" |
| `POST` | `/fibonacci` | Body: `{"number": N}` → computes fib(N), adds custom span attributes |
| `GET` | `/external` | Calls `https://httpbin.org/anything` with propagated trace context |

## What to look for

### Traces
- **`GET /`** — single server span with `http.request.method`, `url.path`, `http.response.status_code` (auto)
- **`POST /fibonacci`** — server span → child `fibonacci.compute` span with `fibonacci.number` + `fibonacci.result` attributes. Try `number: 200` to see an error span.
- **`GET /external`** — server span → child HTTP client span showing W3C `traceparent` propagation. The `httpbin_response.headers` object echoes back the injected header.

### Metrics
- `http.server.request.duration` — auto (agent)
- `http.server.active_requests` — auto (agent) when `OTEL_INSTRUMENTATION_HTTP_SERVER_EMIT_EXPERIMENTAL_TELEMETRY=true`
- `app.fibonacci.input` — manual histogram of valid Fibonacci request numbers, recorded in `FibonacciService`

### Logs
Every SLF4J log line is automatically correlated with the active trace and span IDs by the agent. The console pattern also prints `trace_id` and `span_id` so correlation is visible locally.

## Manual vs auto-instrumentation

| What | How |
|---|---|
| HTTP server spans (`GET /`, `POST /fibonacci`, `GET /external`) | Auto — OTel Java Agent |
| Outbound HTTP span + `traceparent` injection (`/external`) | Auto — agent instruments `RestClient` |
| Log ↔ trace correlation (trace/span ID in log records) | Auto — agent |
| `fibonacci.compute` span | Manual — `@WithSpan("fibonacci.compute")` |
| `fibonacci.number` input attribute | Manual — `@SpanAttribute` |
| `fibonacci.result` output attribute | Manual — `Span.current().setAttribute(...)` |
| `error.type` attribute on bad input | Manual — `ApiExceptionHandler` sets it on validation failures, and the controller sets it for `/external` errors |
| `http.server.active_requests` | Auto — emitted by the Java agent when `OTEL_INSTRUMENTATION_HTTP_SERVER_EMIT_EXPERIMENTAL_TELEMETRY=true` |
| `app.fibonacci.input` histogram | Manual — recorded through `MetricsService` from `FibonacciService.compute(...)` |

## Validation

```bash
# Basic hello world
curl http://localhost:8085/
# → Hello, World!

# Fibonacci
curl -X POST http://localhost:8085/fibonacci \
  -H "Content-Type: application/json" \
  -d '{"number": 10}'
# → {"number":10,"result":55}

# Bad input — expect 422 + error span
curl -X POST http://localhost:8085/fibonacci \
  -H "Content-Type: application/json" \
  -d '{"number": 200}'
# → {"error":"number must be between 0 and 92"}

# External call — check traceparent propagation
curl http://localhost:8085/external
# Look for "Traceparent" in the httpbin_response.headers field
```

## Notes

- Resource attributes set: `service.name`, `service.version=0.1.0`, `deployment.environment=dev`
- Context propagation: W3C TraceContext (enabled by default in the agent)
- The `run` target enables `OTEL_INSTRUMENTATION_HTTP_CLIENT_EMIT_EXPERIMENTAL_TELEMETRY=true` and `OTEL_INSTRUMENTATION_HTTP_SERVER_EMIT_EXPERIMENTAL_TELEMETRY=true`
- `app.fibonacci.input` is a custom business metric that buckets valid Fibonacci request numbers at `1, 2, 3, 5, 8, 13, 21, 34, 55, 89`
- Invalid `/fibonacci` payloads return HTTP `422` with a JSON body like `{"error":"number must be between 0 and 92"}`
- The agent JAR is gitignored; it lives in `agent/` and is downloaded by `make download-agent`
- All OTel config is done via environment variables — nothing is hardcoded in the app
