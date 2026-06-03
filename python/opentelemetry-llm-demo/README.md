# OpenTelemetry NBA Agent Demo

A small FastAPI demo that shows how OpenTelemetry works with a session-aware NBA assistant built with the OpenAI Agents SDK.

The app is intentionally narrow:
- one primary endpoint
- one agent
- one small tool for win percentage
- one input guardrail
- OpenAI-managed conversation sessions

That is enough to produce telemetry that feel meaningfully LLM- and agent-oriented without turning the sample into a bigger product.

## what this demonstrates

- a FastAPI request span for each chat turn
- agent workflow spans from the OpenAI Agents SDK
- model call spans against the OpenAI Responses API
- OpenAI-managed session continuity across turns
- input guardrail checks and guardrail-triggered rejections
- optional GenAI content capture on spans

## prerequisites

- Python 3.12
- an `OPENAI_API_KEY`
- an OTLP endpoint if you want to export telemetry to SigNoz or another backend

### Using SigNoz
1. Sign up for a free account: [Sign up for a free account](https://signoz.io/teams/) if you haven't already.
2. Get your key: Get your key from `Settings -> Ingestion`.

Install dependencies:

```bash
pip install -r requirements.txt
```

## run the demo

Run the application via:

```bash
cd python/opentelemetry-llm-demo

OPENAI_API_KEY="<your-openai-api-key>" \
OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.<your-region>.signoz.cloud:443" \
OTEL_EXPORTER_OTLP_HEADERS="signoz-ingestion-key=<your-ingestion-key>" \
OTEL_SERVICE_NAME="opentelemetry-llm-demo" \
OTEL_RESOURCE_ATTRIBUTES="service.version=0.1.0,deployment.environment=dev" \
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
opentelemetry-instrument fastapi run --port 8085 --workers 1
```

If you explicitly want to disable prompt/response content on spans, use:

```bash
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=0
```

## content capture note

If content capture is enabled, be aware that `gen_ai.input.messages` can include not just the latest user message but the effective model input for that turn. Because this app uses session-backed conversations, that may include earlier turns from the same conversation as well.

## API

### `GET /`

Simple health check:

```bash
curl "http://127.0.0.1:8085/"
```

### `POST /agent/turn`

Runs one conversational turn. If you omit `session_id`, the SDK creates a new OpenAI conversation during the turn and the response returns its ID. Reuse that `session_id` on later calls to preserve context.

Supported `topic` values:
- `eastern`
- `western`
- `finals`
- `general`

Example first turn:

```bash
curl -X POST "http://127.0.0.1:8085/agent/turn" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "eastern",
    "message": "Give me a quick update on the eastern conference finals."
  }'
```

Example follow-up turn with conversation continuity:

```bash
curl -X POST "http://127.0.0.1:8085/agent/turn" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "eastern",
    "session_id": "conv_...",
    "message": "Based on that, who is the safer Finals pick and why?"
  }'
```

Example tool-oriented turn:

```bash
curl -X POST "http://127.0.0.1:8085/agent/turn" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "general",
    "message": "The Raptors went 46-36 this NBA season. What was their win percentage?"
  }'
```

## response shape

Typical successful response:

```json
{
  "topic": "general",
  "session_id": "conv_...",
  "message": "The Raptors finished 46-36, which works out to a .561 winning percentage.",
  "model": "gpt-5.4-mini-2026-03-17",
  "usage": {
    "input_tokens": 123,
    "output_tokens": 45,
    "total_tokens": 168
  }
}
```

The `message` field is intentionally sanitized before returning:
- markdown links are stripped
- bare URLs are stripped
- leftover citation fragments are cleaned up

This keeps the API response readable even when the underlying model used web search.

## guardrails

The demo includes an input guardrail that keeps the assistant focused on NBA and basketball-related requests.

If the guardrail blocks a request, the API returns `400` with the guardrail message. The trace still shows the guardrail span data, and the app also records the handled guardrail exception for visibility in tracing UIs.

## what to look for in traces

A good trace for this demo should usually show:
- `POST /agent/turn`
- agent workflow activity
- a model call to the OpenAI Responses API
- conversation session reads/writes
- guardrail checks
- tool use when you ask a stats-style question

This is enough for the sample to feel agentic without needing a second report-generation flow.
