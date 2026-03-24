# OpenTelemetry Spring Boot Demo

Demonstrates OpenTelemetry instrumentation for a Spring Boot 3.3 application using:
- **OTel Java Agent** for zero-code auto-instrumentation (HTTP server spans, outbound HTTP client spans with W3C trace context propagation, log correlation)
- **`@WithSpan` + `@SpanAttribute`** for business-logic span enrichment (fibonacci computation)
- **OTel API** (`GlobalOpenTelemetry`) for custom metric implementation

## Stack

- Runtime: Java 21
- Framework: Spring Boot 3.3.x + Spring MVC (Tomcat)
- OTel Agent: `opentelemetry-javaagent` 2.12.0
- OTel API: `opentelemetry-api` 1.47.0
- Annotations: `opentelemetry-instrumentation-annotations` 2.12.0
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
OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.<region>.signoz.cloud:443" \
SIGNOZ_INGESTION_KEY="<your-key>" \
make run
```

The server starts on `http://localhost:8085`.

### Generate load

In a separate terminal:

```bash
chmod +x load_gen.sh
./load_gen.sh
```

This continuously generates traffic against `/`, `//`, and `/fibonacci` to produce traces, metrics, and logs until you stop it with `Ctrl-C`.

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
- `http.server.active_requests` — auto (agent)
- `http.server.active_requests` — manual fallback implementation exists in code but is disabled by default
- `app.fibonacci.duration` — custom histogram implementation exists in code but is not recorded by default

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
| `error.type` attribute on bad input | Manual — `Span.current().setAttribute(...)` |
| `http.server.active_requests` fallback | Manual implementation available, disabled by default |
| `app.fibonacci.duration` histogram | Manual implementation available, not recorded by default |

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
- `demo.metrics.manual-http-server-active-requests.enabled=false` keeps the manual `http.server.active_requests` fallback implemented but disabled by default
- `app.fibonacci.duration` is kept as a reference implementation in `MetricsService`, but the controller does not record it by default
- The agent JAR is gitignored; it lives in `agent/` and is downloaded by `make download-agent`
- All OTel config is done via environment variables — nothing is hardcoded in the app
