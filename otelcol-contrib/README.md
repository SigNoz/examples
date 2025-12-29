# OpenTelemetry Collector Contrib Demo

This folder contains a demonstration setup for the **OpenTelemetry Collector Contrib**, a customized OpenTelemetry Collector build that includes optional contrib components for observability (metrics, traces, logs).

## Overview

The OpenTelemetry Collector is a vendor-agnostic proxy that receives, processes, and exports telemetry data. This setup includes:

- **Receivers**: OTLP (traces & metrics) and Host Metrics collection
- **Processors**: Batch, resource detection, and resource enrichment
- **Exporters**: OTLP (for external backends like SigNoz) and Debug exporter
- **Extensions**: Health checks, profiling (pprof), and inspection pages (zpages)

---

## File Descriptions

### Root Level Files

#### `contrib_load_generator.sh`
Bash script that generates synthetic trace and metric data to test the OpenTelemetry Collector.
- Creates parallel workers to simulate concurrent telemetry events
- Generates random trace IDs and span IDs
- Sends HTTP requests to the collector's OTLP endpoint
- Configurable duration, concurrency, and request frequency
- Useful for load testing and validating collector pipelines

#### `otel-config.yaml`
Main configuration file for the OpenTelemetry Collector.
- **Receivers**: Accepts OTLP traces/metrics via gRPC (port 4317) and HTTP (port 4318); collects host metrics (CPU, memory, filesystem)
- **Processors**: Enriches telemetry with resource attributes, detects system information, batches data for efficiency
- **Exporters**: Sends data to SigNoz backend (replace with your credentials) and outputs debug logs
- **Extensions**: Provides health checks (port 13133), profiling API (port 1777), and z-pages (port 55679) for introspection
- **Service**: Defines two pipelines—metrics and traces—connecting receivers → processors → exporters

#### `values.yaml`
Helm chart configuration file for deploying the collector to Kubernetes.
- Configures the OpenTelemetry Collector Contrib image version (0.142.0)
- Defines Kubernetes service ports for health checks, profiling, and z-pages
- Mirrors the full collector configuration from `otel-config.yaml` in Helm values format
- Used by `helm install` or `helm upgrade` commands to deploy to clusters
- Allows easy credential and endpoint management across environments

---

### Builder Directory

The `builder/` directory contains tooling to compile a custom OpenTelemetry Collector binary with selected components.

#### `builder/builder-config.yaml`
Configuration manifest that specifies which OpenTelemetry components to include in the custom build.
- **Receivers**: OTLP receiver and Host Metrics receiver
- **Processors**: Batch processor, resource detection processor, and resource processor
- **Exporters**: OTLP exporter (for sending data to backends) and Debug exporter (for logging)
- **Extensions**: Health check, pprof (profiling), and z-pages (introspection) extensions
- Read by the OpenTelemetry Collector Builder to generate the collector binary
- All components pinned to version 0.142.0 for consistency

#### `builder/Dockerfile`
Multi-stage Dockerfile that builds a custom collector image.
- Uses `otel/opentelemetry-collector-builder:0.142.0` as the base image
- Installs `git` (required by the builder to fetch component dependencies)
- Switches to a non-root user (10001) for security
- Compiles a custom collector binary based on `builder-config.yaml`
- Output image contains only the selected components, resulting in a smaller binary

#### `builder/ocb`
The OpenTelemetry Collector Builder executable.
- Pre-compiled binary that reads `builder-config.yaml`
- Generates custom Go code for the collector binary
- Handles dependency resolution and builds the final executable
- Can be invoked via Docker or directly on the host

#### `builder/_build/` (Generated Output)
Directory containing auto-generated build artifacts (created when builder runs).
- **main.go**: Generated entry point for the custom collector
- **components.go**: Factory definitions for all selected receivers, processors, exporters, and extensions
- **go.mod**: Go module file with all component dependencies pinned
- Contains the compiled binary `custom-contrib-collector` (platform-specific)

---

## Quick Start

### Option 1: Run Locally

1. Update credentials in `otel-config.yaml`:
   ```yaml
   exporters:
     otlp:
       endpoint: "https://ingest.<your-region>.signoz.cloud:443"
       headers:
         signoz-ingestion-key: "<YOUR-KEY>"
   ```

2. Start the collector (assuming binary is built):
   ```bash
   ./builder/_build/custom-contrib-collector --config otel-config.yaml
   ```

3. In another terminal, generate load:
   ```bash
   bash contrib_load_generator.sh localhost
   ```

### Option 2: Deploy to Kubernetes

1. Install the OpenTelemetry Helm Chart:
   ```bash
   helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
   helm install otel-collector open-telemetry/opentelemetry-collector \
     -f values.yaml -n monitoring --create-namespace
   ```

2. Update ingestion credentials in `values.yaml` before installation.

### Option 3: Build Custom Collector with Docker

1. Build the custom collector image:
   ```bash
   cd builder && docker build -t custom-collector:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 4317:4317 -p 4318:4318 -p 13133:13133 \
     -v $(pwd)/otel-config.yaml:/config.yaml \
     custom-collector:latest --config /config.yaml
   ```

---

## Port Mappings

| Service       | Port  | Protocol | Purpose                          |
|---------------|-------|----------|----------------------------------|
| OTLP gRPC     | 4317  | gRPC     | Receive traces and metrics       |
| OTLP HTTP     | 4318  | HTTP     | Receive traces and metrics       |
| Health Check  | 13133 | HTTP     | Liveness/readiness probes        |
| Profiling     | 1777  | HTTP     | pprof debugging endpoints        |
| Z-Pages       | 55679 | HTTP     | Runtime inspection & traces      |

---

## Architecture

```
Applications
    ↓ (OTLP/gRPC or HTTP)
    ↓
┌─────────────────────────────┐
│  OpenTelemetry Collector    │
├─────────────────────────────┤
│ Receivers (OTLP, HostMet)   │
│ Processors (Batch, Resource)│
│ Exporters (OTLP, Debug)     │
└─────────────────────────────┘
    ↓
    ├→ SigNoz Backend (OTLP exporter)
    └→ Logs (Debug exporter)
```

---

## Customization

To modify the collector components:

1. Edit `builder/builder-config.yaml` to add/remove receivers, processors, or exporters
2. Rebuild the binary in `builder/_build/`
3. Update `otel-config.yaml` to configure the new components
4. Restart the collector

---

## Resources

- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [Collector Contrib Components](https://github.com/open-telemetry/opentelemetry-collector-contrib)
- [SigNoz Setup Guide](https://signoz.io/docs/)
