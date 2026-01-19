import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # Don't preload with OpenTelemetry


def post_fork(server, worker):
    """Reinitialize OpenTelemetry in each worker after fork"""
    if os.getenv("OTEL_SERVICE_NAME"):
        try:
            os.system("opentelemetry-bootstrap --action=install")
            print(f"Worker {worker.pid}: OTEL reinitialized")
        except Exception as e:
            print(f"Worker {worker.pid}: OTEL init failed: {e}")


def when_ready(server):
    print(f"Gunicorn ready with {workers} workers")
