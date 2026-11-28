import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # Important: don't preload when using OpenTelemetry


def post_fork(server, worker):
    """
    Reinitialize OpenTelemetry TracerProvider in each worker after fork.
    
    The OTel SDK's background threads (BatchSpanProcessor, etc.) don't survive
    fork(), so we need to set up a fresh TracerProvider in each worker.
    """
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Build resource with service name from env
    service_name = os.getenv("OTEL_SERVICE_NAME", "fastapi-demo")
    resource = Resource.create({"service.name": service_name})

    # Create a new TracerProvider for this worker
    provider = TracerProvider(resource=resource)

    # Set up the OTLP exporter (reads OTEL_EXPORTER_OTLP_ENDPOINT from env)
    exporter = OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))

    # Register as the global tracer provider
    trace.set_tracer_provider(provider)

    print(f"Worker {worker.pid}: TracerProvider initialized")


def when_ready(server):
    print(f"Gunicorn ready with {workers} workers")
