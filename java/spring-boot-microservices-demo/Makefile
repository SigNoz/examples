.PHONY: download-agent run-inventory run-order run-all

download-agent:
	mkdir -p agent
	curl -L -o agent/opentelemetry-javaagent-2.26.0.jar https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v2.26.0/opentelemetry-javaagent.jar

run-inventory:
	cd inventory-service && \
	export OTEL_SERVICE_NAME=inventory-service && \
	export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 && \
	export OTEL_TRACES_EXPORTER=otlp && \
	export OTEL_METRICS_EXPORTER=otlp && \
	export OTEL_LOGS_EXPORTER=otlp && \
	mvn spring-boot:run -Dspring-boot.run.jvmArguments="-javaagent:../agent/opentelemetry-javaagent-2.26.0.jar"

run-order:
	cd order-service && \
	export OTEL_SERVICE_NAME=order-service && \
	export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 && \
	export OTEL_TRACES_EXPORTER=otlp && \
	export OTEL_METRICS_EXPORTER=otlp && \
	export OTEL_LOGS_EXPORTER=otlp && \
	mvn spring-boot:run -Dspring-boot.run.jvmArguments="-javaagent:../agent/opentelemetry-javaagent-2.26.0.jar"

run-all:
	docker-compose up --build
