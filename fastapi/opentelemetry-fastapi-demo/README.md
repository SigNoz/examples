# opentelemetry-fastapi-demo

Sample FastAPI app instrumented with OpenTelemetry and exporting telemetry to SigNoz Cloud over OTLP. It is intentionally pinned to a conservative, production-friendly version set instead of the latest possible FastAPI and OpenTelemetry releases.

## What this demonstrates

- Auto-instrumented inbound FastAPI request spans
- Auto-instrumented outbound `httpx` spans
- Manual nested spans for application work (`load-item`, `call-httpbin`, `exception-demo`)
- Exception recording and failed span status handling in `/exception`
- Local runs, Docker runs, and Docker Compose runs with the same SigNoz Cloud env var model

## Stack

- Runtime: Python 3.13 in Docker, Python 3.12+ locally
- Framework: FastAPI `0.128.8`
- ASGI server: Uvicorn `0.42.0`
- HTTP client: HTTPX `0.28.1`
- OpenTelemetry: `opentelemetry-distro==0.60b1`, `opentelemetry-instrumentation==0.60b1`, `opentelemetry-exporter-otlp==1.39.1`

## Prerequisites

- Python 3.12+ (`python3 --version`)
- A SigNoz Cloud OTLP endpoint
- A SigNoz ingestion key

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Yes | SigNoz Cloud OTLP endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Usually | Export protocol, typically `grpc` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Yes | SigNoz Cloud auth header, usually `signoz-ingestion-key=...` |
| `OTEL_SERVICE_NAME` | Recommended | Service name shown in your telemetry backend |
| `OTEL_RESOURCE_ATTRIBUTES` | Recommended | Extra resource attributes such as `deployment.environment=demo` |
| `OTEL_TRACES_EXPORTER` | No | Defaults to `console,otlp` in Docker |
| `OTEL_METRICS_EXPORTER` | No | Defaults to `none` in this sample |

## Initial setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
opentelemetry-bootstrap --action=install
```

## Running the app

```bash
OTEL_TRACES_EXPORTER=console,otlp \
OTEL_METRICS_EXPORTER=none \
OTEL_SERVICE_NAME=sample-fastapi-app \
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=local \
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.<region>.signoz.cloud:443 \
OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=<YOUR_INGESTION_KEY> \
OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
opentelemetry-instrument uvicorn app.main:app --host localhost --port 5002
```

Visit the URL: `http://127.0.0.1:5002/` once the app is up and running.

## Build and run with Docker

Build image:
```bash
docker build -t sample-fastapi-app .
```

Run container:
```bash
docker run --rm -p 5002:5002 \
  -e OTEL_SERVICE_NAME=sample-fastapi-app \
  -e OTEL_RESOURCE_ATTRIBUTES=deployment.environment=docker \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.<region>.signoz.cloud:443 \
  -e OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=<YOUR_INGESTION_KEY> \
  -e OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
  sample-fastapi-app
```

## Run with Docker Compose

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.<region>.signoz.cloud:443 \
OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=<YOUR_INGESTION_KEY> \
docker compose up --build
```

## What to look for

- **Traces**: Auto-instrumented server spans for every request, plus nested manual spans from the application code
- **Outbound spans**: `httpx` instrumentation around the `https://httpbin.org/delay/...` call in `/external-api`
- **Manual error handling**: `/exception` records an exception event, sets span status to error, and returns HTTP 500
- **Metrics**: Disabled by default (`OTEL_METRICS_EXPORTER=none`)
- **Logs**: Standard Python logging with exception stack traces

## Manual vs auto-instrumentation

- **Auto**: `opentelemetry-bootstrap` installs FastAPI and HTTPX instrumentation packages automatically
- **Manual spans**: `/items/{item_id}`, `/external-api`, and `/exception` create nested spans for business logic and error handling

## Validation

```bash
curl http://localhost:5002/
curl http://localhost:5002/ping
curl "http://localhost:5002/items/2?q=otel"
curl http://localhost:5002/external-api
curl -i http://localhost:5002/exception
```

Expected responses:
- `/` returns `{"Hello":"World"}`
- `/ping` returns `"pong"`
- `/items/2?q=otel` returns a JSON payload after a simulated delay
- `/external-api` returns `{"status":200}`
- `/exception` returns HTTP 500 and emits an error span

## Send traffic with Locust

```bash
pip install locust
locust -f locustfile.py --headless --users 10 --spawn-rate 1 -H http://localhost:5002
```

## Troubleshooting

- Don't run the app in reload mode while validating instrumentation
- No spans at all:
  - Verify `OTEL_EXPORTER_OTLP_ENDPOINT`
  - Verify `OTEL_EXPORTER_OTLP_PROTOCOL`
  - Verify `OTEL_EXPORTER_OTLP_HEADERS` contains a valid SigNoz ingestion key
- Auto-instrumented spans missing:
  - Confirm app is started with `opentelemetry-instrument` (not plain `uvicorn`)
  - Confirm FastAPI auto-instrumentation is installed: `pip show opentelemetry-instrumentation-fastapi`
  - Confirm HTTPX auto-instrumentation is installed: `pip show opentelemetry-instrumentation-httpx`

## Notes

- Service identity is configured with `OTEL_SERVICE_NAME`
- Resource attributes are additive, for example `deployment.environment=local`
- Context propagation across outbound HTTP calls: yes (via `httpx` instrumentation)
- Python 3.13 is used in Docker to match the more modern samples in this repo
