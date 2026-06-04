# Spring Boot Microservices Distributed Tracing Demo

A clean, simple distributed tracing demo using Spring Boot 3, Java 21, and OpenTelemetry automatic instrumentation with SigNoz. This demo showcases how a simple order-service communicates with an inventory-service and how their interaction is traced as a single distributed trace.

## Stack
- Java 21
- Spring Boot 3.5.0 (Spring MVC / Tomcat)
- OpenTelemetry Java Agent (v2.26.0)
- Docker & Docker Compose

## Architecture

```text
                     +-------------------+
POST /orders         |                   |      GET /inventory/{id}
-------------------> |   order-service   | ------------------------+
                     |   (Port 8081)     |                         |
                     +-------------------+                         |
                              |                                    v
                              |                          +-------------------+
                              |                          |                   |
                              +------------------------> | inventory-service |
                              |        (OTLP)            |   (Port 8082)     |
                              |                          +-------------------+
                              |                                    |
                              v                                    |
                     +-------------------+                         |
                     |      SigNoz       | <-----------------------+
                     | (OTel Collector)  |         (OTLP)
                     +-------------------+
```

## Prerequisites
- Java 21+
- Maven 3.9+
- Docker and Docker Compose
- SigNoz running locally (see below) or a SigNoz Cloud account

### Run SigNoz locally
```bash
git clone https://github.com/SigNoz/signoz.git
cd signoz
docker compose -f deploy/docker/docker-compose.yaml up -d
```
Open http://localhost:8080 to access your SigNoz dashboard.

## Run it

### 1. Download OpenTelemetry Agent
First, download the OpenTelemetry Java Agent:
```bash
make download-agent
```

### Local Run
Run the services locally on your machine. Both services will look for a SigNoz collector at `http://localhost:4317`.

Start inventory-service (Terminal 1):
```bash
make run-inventory
```

Start order-service (Terminal 2):
```bash
make run-order
```

### Docker Run
Alternatively, run both services together using Docker Compose. They will look for a SigNoz collector at `http://host.docker.internal:4317`.

```bash
make run-all
```

## What to look for

### Traces
1. Go to SigNoz > Traces.
2. Look for traces where `Service` is `order-service` and `Operation` is `POST /orders`.
3. Click on the trace to see the span breakdown. You should see:
   - `POST /orders` (auto-instrumented Spring Web span)
   - `order.process` (manual span via `@WithSpan`)
   - `GET /inventory/{productId}` (auto-instrumented RestClient span)
   - `GET /inventory/{productId}` (auto-instrumented Spring Web span on inventory-service)
   - `inventory.check` (manual span via `@WithSpan`)

### Metrics
Go to SigNoz > Dashboard. You'll automatically start seeing JVM metrics, HTTP server metrics, and Tomcat metrics from both `order-service` and `inventory-service` without writing any custom metric code.

### Logs
Go to SigNoz > Logs. Because we enabled `OTEL_LOGS_EXPORTER=otlp`, application logs are automatically captured and correlated with your traces.

## Manual vs auto-instrumentation table

| Component | Approach | Description |
|-----------|----------|-------------|
| **HTTP Inbound** | Auto | OpenTelemetry Java Agent automatically intercepts incoming HTTP requests (Tomcat/Spring MVC) and creates spans. |
| **HTTP Outbound** | Auto | OpenTelemetry Java Agent intercepts `RestClient` calls and propagates the W3C trace context via HTTP headers. |
| **Service Logic** | Manual | We use `@WithSpan` and `@SpanAttribute` to add custom business logic spans (`order.process`, `inventory.check`) to the auto-generated trace. |

## Validation

Here are a few `curl` commands to test the application.

**1. Happy Path (In Stock)**
```bash
curl -X POST http://localhost:8081/orders \
-H "Content-Type: application/json" \
-d '{"productId": "P001", "quantity": 2}'
```
*Expected response:* `200 OK` with order details and status `SUCCESS`.

**2. Out of Stock**
```bash
curl -X POST http://localhost:8081/orders \
-H "Content-Type: application/json" \
-d '{"productId": "P002", "quantity": 1}'
```
*Expected response:* `400 Bad Request` with `{"error": "Product out of stock"}`.

**3. Product Not Found**
```bash
curl -X POST http://localhost:8081/orders \
-H "Content-Type: application/json" \
-d '{"productId": "UNKNOWN", "quantity": 1}'
```
*Expected response:* `404 Not Found` with `{"error": "Product not found"}`.

**4. Service Down (Stop inventory-service)**
```bash
curl -X POST http://localhost:8081/orders \
-H "Content-Type: application/json" \
-d '{"productId": "P001", "quantity": 2}'
```
*Expected response:* `503 Service Unavailable` with `{"error": "Inventory service down"}`.

## Notes
- We do not use Lombok to keep the code as simple and beginner-friendly as possible.
- No database is used; products are hardcoded in the `InventoryService`.
- Both services are configured to explicitly send traces, metrics, and logs via OTLP.

## Available Test Products
| Product ID | Name | Stock |
|---|---|---|
| P001 | Laptop | 10 (in stock) |
| P002 | Smartphone | 0 (out of stock) |
| P003 | Headphones | 50 (in stock) |
| P004 | Monitor | 5 (in stock) |
