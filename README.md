# OpenTelemetry Sample Apps

A curated set of minimal, runnable samples that show how to instrument applications with OpenTelemetry across multiple languages and frameworks. Each sample is self-contained with clear run instructions and uses OTLP exporters by default.

## Repository layout
- `templates/` – shared templates and checklists for new samples.
- `golang/`, `python/`, `nodejs/`, `flask/`, `fastapi/`, `dot-net/`, `java/` – language/framework-specific samples organized by app folder.
- Every sample folder includes its own `README.md` with setup, run, and instrumentation notes.

Suggested tree (what we have now):
```
examples/
├── README.md
├── templates/
│   └── SAMPLE_README.md
├── golang/
├── python/
├── nodejs/
├── flask/
├── fastapi/
├── dot-net/
└── java/
```

## Conventions for samples
- Prefer OTLP exporters with env var config (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`).
- Always set `OTEL_SERVICE_NAME` and useful resource attributes (e.g., `deployment.environment`).
- Keep samples minimal: one service, in-memory state, no external DB unless the sample is about DB instrumentation.
- Show both manual spans and auto-instrumentation when possible; note which is enabled by default.
- Include `docker compose` or a local OTLP/collector hint when practical.
- Add a short “What this demonstrates” section and expected telemetry (traces/metrics/logs).

## How to add a new sample
1. Pick the language/framework folder (or create a new one) and add an app directory with a descriptive name.
2. Copy `templates/SAMPLE_README.md` into the app folder and fill it out.
3. Keep runtimes pinned (e.g., Go 1.22, Node 20, Python 3.11) and list them.
4. Provide a one-command start (`make run`, `npm run start`, `go run main.go`, etc.).
5. Add minimal validation instructions (curl the endpoint, view spans/metrics/logs).

