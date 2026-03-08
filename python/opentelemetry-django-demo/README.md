# sample-django

Sample Django app instrumented with OpenTelemetry and exporting traces directly to SigNoz (OTLP).

## Prerequisites

- Python 3.12+ (3.13 recommended)
- `pip`
- SigNoz OTLP ingest endpoint and ingestion key

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
opentelemetry-bootstrap --action=install
```

## Run locally with Gunicorn

```bash
DJANGO_SETTINGS_MODULE=mysite.settings \
OTEL_TRACES_EXPORTER=console,otlp \
OTEL_METRICS_EXPORTER=none \
OTEL_RESOURCE_ATTRIBUTES=service.name=sample-django-app \
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.<region>.signoz.cloud:443 \
OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=<YOUR_INGESTION_KEY> \
OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
opentelemetry-instrument gunicorn mysite.wsgi -c gunicorn.config.py --workers 2 --threads 2
```

Open the app:
- `http://127.0.0.1:8000/polls/`
- `http://127.0.0.1:8000/admin/`

## Build and run with Docker

Build image:
```bash
docker build -t sample-django-app .
```

Run container:
```bash
docker run --rm -p 8000:8000 \
  -e DJANGO_SETTINGS_MODULE=mysite.settings \
  -e OTEL_TRACES_EXPORTER=console,otlp \
  -e OTEL_METRICS_EXPORTER=none \
  -e OTEL_RESOURCE_ATTRIBUTES=service.name=sample-django-app \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.<region>.signoz.cloud:443 \
  -e OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=<YOUR_INGESTION_KEY> \
  -e OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
  sample-django-app
```

## Troubleshooting

- Manual spans appear but Django request spans do not:
  - Confirm app is started with `opentelemetry-instrument` (not plain `gunicorn`)
  - Confirm Django auto instrumentation is installed:
    - `pip show opentelemetry-instrumentation-django`
  - Avoid reload mode while testing (`--reload` can break forked instrumentation startup)
- No spans at all:
  - Verify `OTEL_EXPORTER_OTLP_ENDPOINT`
  - Verify `OTEL_EXPORTER_OTLP_HEADERS` includes a valid `signoz-ingestion-key`
