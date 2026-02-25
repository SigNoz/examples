# How to Run the App

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.<region>.signoz.cloud:443" \
SIGNOZ_INGESTION_KEY="<your-signoz-key>" \
OTEL_RESOURCE_ATTRIBUTES="service.name=opentelemetry-rust-demo,service.version=0.1.0,deployment.environment=dev"
cargo run
```
