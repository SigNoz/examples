# OpenTelemetry Collector Contrib Demo

This folder contains a comprehensive demonstration setup for the **OpenTelemetry Collector Contrib**. It covers deploying the standard Contrib distribution via Docker and Kubernetes, as well as building a custom, optimized Collector binary using the OpenTelemetry Collector Builder (OCB).

## Overview

The OpenTelemetry Collector Contrib distribution includes a vast ecosystem of community-maintained receivers, processors, and exporters. This setup demonstrates:

- **Receivers**: OTLP (gRPC/HTTP), Host Metrics (CPU, RAM, Disk), and Filelog.
- **Processors**: Batching, Resource Detection (Cloud/System metadata), and Attributes modification.
- **Exporters**: OTLP (sending data to SigNoz) and Debug (logging to console).
- **Extensions**: Health checks, Pprof (profiling), and zPages (introspection).

## Prerequisites

1.  **SigNoz Account**: You need an ingestion key to send data to SigNoz.
    - [Sign up for a free account](https://signoz.io/teams/) if you haven't already.
    - Get your key from `Settings -> Ingestion`.
2.  **Git**: Clone this repository to access the config files.
    ```bash
    git clone git@github.com:SigNoz/examples.git
    cd examples/otelcol-contrib
    ```

---

## 🚀 Quick Start

### Method 1: Docker (Recommended for Testing)

Run the official Contrib image with our custom configuration.

1.  **Update Configuration**:
    Open `otel-config.yaml` and replace `<SIGNOZ-INGESTION-KEY>` and `<region>` with your actual values.

2.  **Run Container**:
    ```bash
    docker run \
      -v $(pwd)/otel-config.yaml:/etc/otelcol-contrib/config.yaml \
      -p 4317:4317 -p 4318:4318 \
      -p 13133:13133 -p 1777:1777 -p 55679:55679 \
      --rm --name otelcol-contrib \
      otel/opentelemetry-collector-contrib:0.142.0
    ```

3.  **Verify**:
    ```bash
    curl localhost:13133
    # Output: Server available
    ```

### Method 2: Kubernetes (Helm)

Deploy the collector to a Kubernetes cluster using the official Helm chart and our `values.yaml`.

1.  **Update Configuration**:
    Open `values.yaml` and update the `config.exporters.otlp` section with your SigNoz region and Ingestion Key.

2.  **Install Chart**:
    ```bash
    helm repo add open-telemetry [https://open-telemetry.github.io/opentelemetry-helm-charts](https://open-telemetry.github.io/opentelemetry-helm-charts)
    helm install -f values.yaml otelcol-contrib open-telemetry/opentelemetry-collector
    ```

3.  **Access Collector Locally**:
    Forward ports to your local machine to verify or send test data:
    ```bash
    kubectl port-forward svc/otelcol-contrib-opentelemetry-collector \
      4317:4317 4318:4318 13133:13133 1777:1777 55679:55679
    ```

---

## 🛠️ Advanced: Build Your Own Collector

If you want to reduce binary size and improve security, you can build a custom distribution containing *only* the components you need using the **OpenTelemetry Collector Builder (OCB)**.

### 1. Setup OCB
Download the builder binary for your architecture (example for Linux AMD64):
```bash
cd builder

curl --proto '=https' --tlsv1.2 -fL -o ocb \
[https://github.com/open-telemetry/opentelemetry-collector/releases/download/cmd%2Fbuilder%2Fv0.120.0/ocb_0.120.0_linux_amd64](https://github.com/open-telemetry/opentelemetry-collector/releases/download/cmd%2Fbuilder%2Fv0.120.0/ocb_0.120.0_linux_amd64)

chmod +x ocb
```

### 2. Compile
We use `builder-config.yaml` to define the exact components to include.
```bash
./ocb --config builder-config.yaml
```
*This generates a `_build` directory containing your custom binary.*

### 3. Run Custom Binary
Run the newly built collector using the standard configuration file:
```bash
./_build/custom-contrib-collector --config ../otel-config.yaml
```

---

## ⚡ Generating Traffic

We provide a script to generate synthetic OTLP traces and metrics to verify your pipeline.

1.  **Make executable**:
    ```bash
    chmod +x contrib_load_generator.sh
    ```

2.  **Run Generator**:
    ```bash
    # Usage: ./contrib_load_generator.sh <HOST>
    ./contrib_load_generator.sh localhost
    ```
    *This will send data to port `4318` (HTTP OTLP) for 30 seconds.*

---

## 📂 File Structure & Descriptions

### Configuration Files

| File | Description |
|------|-------------|
| `otel-config.yaml` | **Main Collector Config.** Defines the pipeline: <br>• **Receivers:** `otlp`, `hostmetrics` <br>• **Processors:** `resourcedetection` (system info), `resource` (tags), `batch` <br>• **Exporters:** `otlp` (SigNoz), `debug` |
| `values.yaml` | **Helm Config.** Overrides for the `open-telemetry/opentelemetry-collector` chart. Contains a replica of the config in `otel-config.yaml` formatted for Helm. |
| `contrib_load_generator.sh` | **Traffic Gen.** A Bash script that sends dummy telemetry (traces/metrics) to the collector via `curl`. |

### Builder Directory (`/builder`)

| File | Description |
|------|-------------|
| `builder-config.yaml` | **Manifest.** Lists the specific Go modules (receivers/processors/exporters) to include in the custom build. |
| `Dockerfile` | **Multi-stage Build.** A Dockerfile that uses OCB to compile the binary and packages it into a minimal production image. |
| `_build/` | **Artifacts.** (Created after running OCB) Contains the compiled binary `custom-contrib-collector`. |

---

## Architecture

```text
+-------------------+       +---------------------------------------------+
|    Application    |       |             OpenTelemetry Collector         |
|   (Load Gen)      |       |                                             |
+--------+----------+       |    +-----------+    +---------+    +-----+  |
         | OTLP             |    |           |    |         |    |     |  |
         v                  |    | Receivers +--->+ Processors+--->+ Exp  |
+--------+----------+       |    |           |    |         |    |     |  |
|    Host Metrics   |       |    +-----+-----+    +---------+    +--+--+  |
|      (CPU/RAM)    +------>+          ^                            |     |
+-------------------+       |          |                            |     |
                            +---------------------------------------+-----+
                                       |                            |
                                       |                            |
                                  +----+-----+               +------+-----+
                                  |  Console |               |   SigNoz   |
                                  |  (Debug) |               |   Cloud    |
                                  +----------+               +------------+
```

## Useful Ports

| Port | Protocol | Usage |
|------|----------|-------|
| `4317` | gRPC | OTLP Receiver (Traces/Metrics) |
| `4318` | HTTP | OTLP Receiver (Traces/Metrics) |
| `13133` | HTTP | Health Check Extension |
| `1777` | HTTP | pprof Profiling Extension |
| `55679`| HTTP | zPages Extension |

## Resources

- [OpenTelemetry Collector Docs](https://opentelemetry.io/docs/collector/)
- [SigNoz Documentation](https://signoz.io/docs/)
- [OCB (Builder) Documentation](https://opentelemetry.io/docs/collector/custom-collector/)
