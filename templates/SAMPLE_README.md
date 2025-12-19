# Sample Name

Brief description of what this sample demonstrates (e.g., basic HTTP tracing with OTLP exporter, auto-instrumentation only).

## Stack
- Runtime: <language version>
- Framework/libs: <framework versions>
- OpenTelemetry libs: <package names/versions>

## Run it
```bash
# set OTLP target if not using defaults
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=<service-name>

# install deps
<install command>

# start app
<start command>
```

## What to look for
- Traces: <endpoints/operations expected>
- Metrics: <key meters/instruments>
- Logs: <structured logs?>

## Manual vs auto-instrumentation
- Manual spans: <where created>
- Auto: <which instrumentation packages enabled>

## Validation
- `curl http://localhost:PORT/...` -> expect <response>
- Check spans/metrics in collector/console: <instructions>

## Notes
- Resource attributes set: `service.name`, `deployment.environment`, ...
- Context propagation across outbound calls? <yes/no>
- Anything unusual or caveats.
