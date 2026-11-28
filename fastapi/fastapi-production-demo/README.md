# FastAPI Production Demo

FastAPI app with OpenTelemetry instrumentation, configured for production with Gunicorn workers.

Shows:
- FastAPI auto-instrumentation
- Gunicorn with Uvicorn workers
- Worker initialization for OpenTelemetry (handles forking issue)
- Manual span creation
- Error handling with spans

## Stack

- **Runtime:** Python 3.11+
- **Framework:** FastAPI 0.115.0
- **ASGI Server:** Uvicorn 0.32.0
- **WSGI Server:** Gunicorn 23.0.0 (for production)
- **OpenTelemetry:** opentelemetry-distro 0.45b0, opentelemetry-exporter-otlp 1.27.0

## Prerequisites

- Python 3.11 or newer
- SigNoz instance (cloud or self-hosted)
- OTLP endpoint accessible (default: `http://localhost:4317` for self-hosted)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install OpenTelemetry Instrumentation

```bash
opentelemetry-bootstrap --action=install
```

### 3. Set Environment Variables

For **SigNoz Cloud**:
```bash
export OTEL_SERVICE_NAME=fastapi-production-demo
export OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.<REGION>.signoz.cloud:443
export OTEL_EXPORTER_OTLP_HEADERS="signoz-ingestion-key=<YOUR_INGESTION_KEY>"
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
```

For **Self-hosted SigNoz**:
```bash
export OTEL_SERVICE_NAME=fastapi-production-demo
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_RESOURCE_ATTRIBUTES="deployment.environment=production"
```

### 4. Run the Application

**Development (single process):**
```bash
opentelemetry-instrument uvicorn app:app --host 0.0.0.0 --port 8000
```

**Production (with Gunicorn workers):**
```bash
opentelemetry-instrument gunicorn app:app -c gunicorn_config.py
```

## Endpoints

- `GET /` - Root endpoint with service info
- `GET /health` - Health check
- `GET /api/users/{user_id}` - Get user by ID (simulates DB query)
- `GET /api/users/{user_id}/orders` - Get user orders (shows nested spans)
- `GET /api/metrics/demo` - Metrics demonstration endpoint

## What to Look For

In SigNoz, you should see:
- HTTP request spans (auto-created)
- Custom spans for DB queries and API calls
- Nested spans showing operation flow
- Error spans when things fail

Auto-instrumentation handles HTTP requests. Manual spans are used for DB queries and external calls.

## Production Deployment

### Gunicorn Configuration

The `gunicorn_config.py` includes a `post_fork` hook that creates a fresh TracerProvider in each worker process. This is necessary because the OTel SDK's background threads (BatchSpanProcessor, etc.) don't survive `fork()`. Without this, spans from worker processes won't export.

### Worker Count

Adjust based on your workload:
```bash
export WORKERS=4  # Default
opentelemetry-instrument gunicorn app:app -c gunicorn_config.py
```

For CPU-bound workloads: `workers = (2 × CPU cores) + 1`
For I/O-bound workloads: `workers = (4 × CPU cores) + 1`

### Docker Deployment

Example Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap --action=install

COPY . .

EXPOSE 8000

CMD ["opentelemetry-instrument", "gunicorn", "app:app", "-c", "gunicorn_config.py"]
```

## Troubleshooting

### Missing Spans with Multiple Workers

If spans are missing with Gunicorn workers, it's because the OpenTelemetry SDK's background threads (BatchSpanProcessor) don't survive `fork()`. The `post_fork` hook in `gunicorn_config.py` creates a fresh TracerProvider in each worker - it's already set up.

### Spans Not Appearing in SigNoz

1. **Check OTLP endpoint:**
   ```bash
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   ```

2. **Verify connectivity:**
   ```bash
   curl $OTEL_EXPORTER_OTLP_ENDPOINT/health
   ```

3. **Check service name:**
   ```bash
   echo $OTEL_SERVICE_NAME
   ```

4. **Enable debug logging:**
   ```bash
   export OTEL_LOG_LEVEL=debug
   ```

### Hot Reload Issues

**Problem:** Instrumentation breaks when using `--reload` flag.

**Solution:** Don't use `--reload` in production. For development, use single process mode:
```bash
opentelemetry-instrument uvicorn app:app --reload
```

### gRPC vs HTTP Exporter

This example uses gRPC by default. For HTTP:
```bash
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

## Validation

1. **Start the application:**
   ```bash
   opentelemetry-instrument gunicorn app:app -c gunicorn_config.py
   ```

2. **Make test requests:**
   ```bash
   curl http://localhost:8000/
   curl http://localhost:8000/api/users/1
   curl http://localhost:8000/api/users/1/orders
   ```

3. **Check SigNoz:**
   - Navigate to Traces section
   - Filter by service name: `fastapi-production-demo`
   - Verify spans are appearing with proper hierarchy

## Notes

- **Resource attributes:** Set via `OTEL_RESOURCE_ATTRIBUTES` env var
- **Context propagation:** Automatic for HTTP requests via FastAPI instrumentation
- **Worker processes:** Each worker maintains its own OpenTelemetry SDK instance
- **Error handling:** Exceptions are automatically recorded in spans

## Related Documentation

- [SigNoz Python Instrumentation Guide](https://signoz.io/docs/instrumentation/opentelemetry-python/)
- [FastAPI Instrumentation](https://signoz.io/docs/instrumentation/fastapi/)
- [OpenTelemetry Python Multiprocessing](https://opentelemetry-python.readthedocs.io/en/latest/instrumentation/runtime.html#multiprocessing)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
