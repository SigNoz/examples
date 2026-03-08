from opentelemetry import trace


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    # Create a span to verify telemetry is flowing from forked workers.
    tracer = trace.get_tracer("sample-django-app")

    with tracer.start_as_current_span("gunicorn-config-init") as span:
        span.add_event("finished gunicorn config init for worker", {"worker_pid": worker.pid})
