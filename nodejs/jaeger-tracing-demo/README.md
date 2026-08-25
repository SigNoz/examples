# Jaeger Tracing Demo with OpenTelemetry

This demo runs two instrumented Node.js services and sends their distributed traces directly to Jaeger over OTLP/HTTP. It creates normal, slow, and failed checkout requests so you can practice finding latency and following errors across service boundaries in the Jaeger UI.

For a detailed explanation of Jaeger's architecture, tracing workflow, and core concepts, read the [Jaeger tracing guide](https://signoz.io/blog/jaeger-tracing/).

## What this demonstrates

- Automatic HTTP and Express instrumentation with OpenTelemetry
- W3C trace-context propagation between two services
- A manual `inventory.lookup` span with domain-specific attributes
- Span events, error status, and exception recording
- Direct OTLP/HTTP export to Jaeger 2.20
- Automated verification of the generated trace data

## Architecture

```text
Traffic generator
      |
      v
frontend-service :3000
      |
      v
inventory-service :3001
      |
      +--------------------+
                           v
                 Jaeger OTLP/HTTP :4318
                           |
                           v
                    Jaeger UI :16686
```

Both application services run inside Docker Compose. The frontend calls the inventory service using the Compose network, and both services export spans to Jaeger.

## Stack

- Node.js 24.11.1 in the application containers
- Express 5.2.1
- OpenTelemetry Node SDK 0.221.0
- OpenTelemetry Node auto-instrumentations 0.79.0
- Jaeger 2.20.0
- Docker Compose

## Prerequisites

Install the following before starting:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or another Docker installation with Compose
- Node.js 20 or later
- npm

Confirm that Docker is running:

```bash
docker version
docker compose version
```

`docker version` should display both `Client` and `Server` sections.

## Run the demo

Clone this repository and open the demo directory:

```bash
git clone https://github.com/SigNoz/examples.git
cd examples/nodejs/jaeger-tracing-demo
```

Install the local dependencies:

```bash
npm install
```

Start Jaeger and both application services:

```bash
docker compose up --build -d
```

Confirm that the three services are running:

```bash
docker compose ps
```

The output should list `jaeger`, `frontend`, and `inventory` with a running status.

Generate normal, slow, and failed checkout requests:

```bash
npm run traffic
```

The generator sends 20 requests. Normal and slow scenarios return HTTP `200`; deliberately failed inventory requests return HTTP `502` from the frontend.

## View traces in Jaeger

Open [http://localhost:16686](http://localhost:16686), select `frontend-service` from the **Service** menu, and click **Find Traces**.

### Inspect a slow request

Open a trace lasting approximately 700 ms and select its `inventory.lookup` span. The span should contain:

```text
inventory.lookup.mode = slow
```

It also contains a `simulated slow database query` event. The duration of this span shows that the inventory lookup accounts for most of the request latency.

### Inspect a failed request

Open a trace marked with an error and select its `inventory.lookup` span. It should have an `ERROR` status and an exception similar to:

```text
Inventory database timed out for camera-005
```

The complete trace connects the inventory service's HTTP `503` response to the HTTP `502` response returned by the frontend.

## Verify the traces automatically

Run:

```bash
npm run verify
```

The verifier queries Jaeger and checks that:

- `frontend-service` and `inventory-service` occur in the same distributed trace.
- A slow `inventory.lookup` span lasts at least 650 ms and contains the diagnostic event.
- A failed lookup contains the recorded timeout and an `ERROR` status.

Successful output has this structure. Trace IDs, counts, and durations vary between runs:

```json
{
  "serviceNames": [
    "frontend-service",
    "inventory-service"
  ],
  "tracesChecked": 30,
  "slowTrace": {
    "traceID": "<trace-id>",
    "durationMs": 708.472,
    "lookupDurationMs": 703.227
  },
  "failedTrace": {
    "traceID": "<trace-id>",
    "errorSpanCount": 4
  }
}
```

## Generate individual scenarios

Use these requests when you want to create one specific type of trace:

```bash
curl "http://localhost:3000/checkout?sku=camera-001&mode=normal"
curl "http://localhost:3000/checkout?sku=camera-002&mode=slow"
curl "http://localhost:3000/checkout?sku=camera-003&mode=fail"
```

The available modes are:

| Mode | Inventory behavior | Frontend response |
| --- | --- | --- |
| `normal` | Waits about 35 ms and succeeds | HTTP `200` |
| `slow` | Waits about 700 ms and succeeds | HTTP `200` |
| `fail` | Records a timeout and returns HTTP `503` | HTTP `502` |

## How instrumentation works

`instrumentation.mjs` starts the OpenTelemetry Node SDK before Express is imported. HTTP and Express auto-instrumentation create spans at the service boundaries and propagate trace context from the frontend to the inventory service.

The inventory handler adds a manual span for the domain operation:

```js
return tracer.startActiveSpan('inventory.lookup', async (span) => {
  span.setAttribute('inventory.sku', sku)
  span.setAttribute('inventory.lookup.mode', mode)
  // Inventory operation
})
```

The applications export traces to this endpoint inside the Compose network:

```text
http://jaeger:4318/v1/traces
```

`jaeger` is the Compose service name. Port `4318` is Jaeger's OTLP/HTTP receiver, and `/v1/traces` is the standard OTLP/HTTP traces path.

## Project files

| File | Purpose |
| --- | --- |
| `.dockerignore` | Excludes local dependencies and development files from the application image. |
| `compose.yaml` | Runs Jaeger, the frontend service, and the inventory service on one Docker network. It also configures service names and the OTLP endpoint. |
| `Dockerfile` | Builds the shared Node.js image used by both application services. |
| `frontend.mjs` | Exposes `/checkout` and `/health`; calls the inventory service and converts inventory failures into HTTP `502` responses. |
| `inventory.mjs` | Exposes `/stock` and `/health`; creates the manual lookup span and implements normal, slow, and failed scenarios. |
| `instrumentation.mjs` | Initializes the OpenTelemetry SDK, OTLP trace exporter, and Node.js auto-instrumentation. |
| `generate-traffic.mjs` | Waits for the frontend to become ready and sends 20 requests covering all three scenarios. |
| `verify-traces.mjs` | Queries the Jaeger API and asserts that the expected distributed, slow, and failed traces exist. |
| `package.json` | Defines the application dependencies and npm commands. |
| `package-lock.json` | Locks the exact npm dependency versions for reproducible installation. |

## npm commands

| Command | Purpose |
| --- | --- |
| `npm run frontend` | Starts the frontend locally with OpenTelemetry loaded first. |
| `npm run inventory` | Starts the inventory service locally with OpenTelemetry loaded first. |
| `npm run traffic` | Generates normal, slow, and failed requests against the Dockerized frontend. |
| `npm run verify` | Validates the resulting traces through the Jaeger API. |

## Troubleshooting

### Docker cannot connect to the daemon

Start Docker Desktop and wait until `docker version` displays a `Server` section.

### A port is already in use

The demo requires host ports `3000`, `16686`, `4317`, and `4318`. Stop the process using the conflicting port or choose another frontend port without editing the Compose file:

```bash
FRONTEND_PORT=3100 docker compose up --build -d
FRONTEND_URL=http://localhost:3100 npm run traffic
```

When using an alternate frontend port, send individual `curl` requests to that port as well. Ports `16686`, `4317`, and `4318` can be changed on the host side in `compose.yaml` if required.

### No services appear in Jaeger

Generate traffic with `npm run traffic`, wait a few seconds for the batch exporter to flush, and refresh the Jaeger UI. Check the application logs if the services still do not appear:

```bash
docker compose logs frontend inventory
```

### Containers exit during startup

Inspect all container logs:

```bash
docker compose logs
```

Rebuild the application image after changing dependencies or source files:

```bash
docker compose up --build -d
```

## Stop and clean up

Stop and remove the demo containers and network:

```bash
docker compose down
```

Jaeger uses transient in-memory storage in this demo, so stored traces disappear when the Jaeger container is removed.

## Production note

This project is a local learning environment. A production Jaeger deployment requires decisions about persistent storage, authentication, retention, scaling, sampling, and whether to place an OpenTelemetry Collector between applications and the tracing backend.
