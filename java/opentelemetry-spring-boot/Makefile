.DEFAULT_GOAL := help
AGENT_JAR := agent/opentelemetry-javaagent.jar

.PHONY: help download-agent run clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

download-agent: ## Download the OTel Java Agent JAR (run once)
	@bash scripts/download_agent.sh

## associate the AGENT_JAR file's existence with the download-agent target
$(AGENT_JAR): download-agent

run: $(AGENT_JAR) ## Start the demo app with the OTel Java Agent attached
	@: $${OTEL_EXPORTER_OTLP_ENDPOINT:?'OTEL_EXPORTER_OTLP_ENDPOINT is not set. Example: https://ingest.us.signoz.cloud:443'}
	@: $${SIGNOZ_INGESTION_KEY:?'SIGNOZ_INGESTION_KEY is not set. Get it from your SigNoz Cloud ingestion keys page.'}
	OTEL_SERVICE_NAME=opentelemetry-spring-boot-demo \
	OTEL_EXPORTER_OTLP_ENDPOINT=$(OTEL_EXPORTER_OTLP_ENDPOINT) \
	OTEL_EXPORTER_OTLP_HEADERS="signoz-ingestion-key=$(SIGNOZ_INGESTION_KEY)" \
	OTEL_RESOURCE_ATTRIBUTES="service.version=0.1.0,deployment.environment=dev" \
	OTEL_METRIC_EXPORT_INTERVAL=10000 \
	OTEL_JAVA_DISABLED_RESOURCE_PROVIDERS=io.opentelemetry.instrumentation.resources.ProcessResourceProvider \
	OTEL_INSTRUMENTATION_HTTP_CLIENT_EMIT_EXPERIMENTAL_TELEMETRY=true \
	OTEL_INSTRUMENTATION_HTTP_SERVER_EMIT_EXPERIMENTAL_TELEMETRY=true \
	mvn spring-boot:run \
	  -Dspring-boot.run.jvmArguments="-javaagent:$(AGENT_JAR)"

clean: ## Remove build artifacts and downloaded agent
	mvn clean
	rm -rf agent/
