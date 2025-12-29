"""
Python OOM demo exporting traces, logs, and metrics to SigNoz via OTLP.
Purpose: create a controlled memory ramp and observe it across signals.
"""

import logging
import os
import sys
import time
import psutil

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.metrics import Observation

# Default service name if OTEL_SERVICE_NAME is not set
DEFAULT_SERVICE_NAME = "python-oom-demo"


def configure_resource() -> Resource:
    # Attach service identity to all telemetry
    service_name = os.getenv("OTEL_SERVICE_NAME") or DEFAULT_SERVICE_NAME
    return Resource.create({"service.name": service_name})


def configure_tracing(resource: Resource) -> BatchSpanProcessor:
    # Configure OTLP trace export pipeline
    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(OTLPSpanExporter())
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    return span_processor


def configure_logging(resource: Resource) -> tuple[LoggerProvider, BatchLogRecordProcessor]:
    # Configure OTLP log export pipeline
    logger_provider = LoggerProvider(resource=resource)
    log_processor = BatchLogRecordProcessor(OTLPLogExporter())
    logger_provider.add_log_record_processor(log_processor)

    # Auto-instrument standard logging module
    LoggingInstrumentor().instrument(
        set_logging_format=True,
        logger_provider=logger_provider,
    )

    # Bridge Python logging records into OpenTelemetry logs
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    return logger_provider, log_processor


def configure_metrics(resource: Resource) -> tuple[MeterProvider, PeriodicExportingMetricReader]:
    # Periodically export metrics over OTLP
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(),
        export_interval_millis=5000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Explicit RSS gauge to create a clear memory ramp signal
    meter = metrics.get_meter(__name__)
    process = psutil.Process()

    def _rss_callback(_options) -> list[Observation]:
        # Pull live RSS from the current process
        return [Observation(process.memory_info().rss, {"state": "rss"})]

    meter.create_observable_gauge(
        name="process.memory.rss",
        callbacks=[_rss_callback],
        unit="By",
        description="Resident set size of the current process",
    )

    return meter_provider, metric_reader


def configure_system_metrics():
    # Auto-emit process and system memory metrics
    SystemMetricsInstrumentor().instrument()


def ramp_memory_and_fail(chunk_mb: int, sleep_seconds: float):
    tracer = trace.get_tracer(__name__)
    logger = logging.getLogger(__name__)

    allocations: list[bytearray] = []
    chunk_bytes = chunk_mb * 1024 * 1024

    # Optional soft cap to trigger MemoryError deterministically
    max_mb_env = 400
    max_bytes = max_mb_env * 1024 * 1024 if max_mb_env else None

    with tracer.start_as_current_span("oom-demo") as span:
        # Add ramp parameters for trace correlation
        span.set_attribute("demo.chunk_mb", chunk_mb)
        span.set_attribute("demo.sleep_seconds", sleep_seconds)
        if max_bytes:
            span.set_attribute("demo.max_bytes", max_bytes)

        logger.info("Starting memory ramp", extra={"chunk_mb": chunk_mb})

        try:
            i = 0
            while True:
                # Allocate memory in fixed chunks to simulate pressure
                allocations.append(bytearray(chunk_bytes))
                i += 1
                logger.info(
                    "Allocated chunk",
                    extra={"chunk_index": i, "allocated_mb": i * chunk_mb},
                )

                # Force MemoryError instead of OS-level OOM kill
                if max_bytes and (i * chunk_bytes) >= max_bytes:
                    raise MemoryError(
                        f"Reached demo cap of {max_bytes / (1024 * 1024):.1f} MB"
                    )

                time.sleep(sleep_seconds)

        except MemoryError as exc:
            # Surface failure across logs and traces
            logger.exception("MemoryError triggered; demo complete")
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def main():
    # Initialize all telemetry pipelines
    resource = configure_resource()
    span_processor = configure_tracing(resource)
    logger_provider, log_processor = configure_logging(resource)
    meter_provider, metric_reader = configure_metrics(resource)
    configure_system_metrics()

    # Ramp configuration
    chunk_mb = int(os.getenv("OOM_CHUNK_MB", "10"))
    sleep_seconds = float(os.getenv("OOM_SLEEP_SECONDS", "0.5"))

    try:
        ramp_memory_and_fail(chunk_mb, sleep_seconds)
    except MemoryError:
        # Non-zero exit without kernel OOM kill
        sys.exit(1)
    finally:
        # Flush telemetry before shutdown
        span_processor.shutdown()
        log_processor.shutdown()
        metric_reader.shutdown()
        logger_provider.shutdown()
        meter_provider.shutdown()


if __name__ == "__main__":
    main()
