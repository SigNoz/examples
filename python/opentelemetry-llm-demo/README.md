# OpenTelemetry LLM Demo Application

## how to run?

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.<your-region>.signoz.cloud:443" \
OTEL_EXPORTER_OTLP_HEADERS="signoz-ingestion-key=<your-ingestion-key>" \
OTEL_SERVICE_NAME="opentelemetry-llm-demo" \
OTEL_RESOURCE_ATTRIBUTES="service.version=0.1.0,deployment.environment=dev" \
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
opentelemetry-instrument fastapi run
```

## endpoint

The demo exposes a single endpoint built on the OpenAI Python SDK's
`chat.completions.create(...)` API surface:

```bash
curl "http://127.0.0.1:8000/openai_nba?topic=finals"
```

Supported `topic` values:

- `eastern`
- `western`
- `finals`
- `general`
