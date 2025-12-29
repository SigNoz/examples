# Python OOM Demo

A controlled Out-Of-Memory (OOM) demo application in Python that exports **metrics**, **logs**, and **traces** via **OpenTelemetry (OTLP)** to **SigNoz**.
This demo simulates increasing memory pressure and captures telemetry until a deterministic `MemoryError` occurs.
You can refer to [What is OOM (Out Of Memory)?](https://signoz.io/guides/what-is-oom/) guide for full steps.

## Features

- Gradual memory allocation to simulate memory pressure
- Exports **metrics** for memory usage
- Structured **logs** for allocation steps and exceptions
- **Traces** with error status and recorded exception
- All telemetry shipped over OTLP to SigNoz

## Prerequisites

- Python 3.8+
- [SigNoz Cloud](https://signoz.io/teams/)

## Installation

1. Clone the repo:

    ```bash
    git clone <https://github.com/your-org/python-oom-demo.git>
    cd python-oom-demo
    
    ```

2. Create a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate
    
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    
    ```

## Configuration

Configure the following environment variables before running:

| Variable | Description | Required | Default |
| --- | --- | --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC endpoint for SigNoz | Yes | — |
| `OTEL_EXPORTER_OTLP_HEADERS` | OTLP headers (e.g., auth for SigNoz Cloud) | Yes | — |
| `OTEL_SERVICE_NAME` | Service name shown in the backend | No | `python-oom-demo` |
| `OOM_CHUNK_MB` | Memory allocated per iteration (MB) | No | `10` |
| `OOM_SLEEP_SECONDS` | Delay between allocations (seconds) | No | `0.5` |

Example:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.<REGION>.signoz.cloud:443"
export OTEL_EXPORTER_OTLP_HEADERS="signoz-access-token=<SIGNOZ_INGESTION_API_KEY>"

```

## Usage

Run the demo:

```bash
python main.py

```

The application starts allocating memory incrementally until it hits the configured threshold and raises a `MemoryError`.

Telemetry (logs, metrics, and traces) will be exported continuously to your OTLP backend.

## Signals Observed

- **Metrics**
    - `process.memory.rss`: Resident memory usage

- **Logs**
    - Allocation progress
    - Exception stack trace on OOM

- **Traces**
    - A span named `oom-demo`
    - Error status with exception details

## Exit Behaviour

The demo exits with a **non-zero code** on `MemoryError`, but does not rely on a kernel OOM kill.
Telemetry pipelines are flushed during shutdown.

## **License**

This project is open source and available under the [MIT License](https://github.com/LuffySama-Dev/SampleNodejsExample/blob/main/LICENSE).