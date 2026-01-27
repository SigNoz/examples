# E-Commerce OpenTelemetry Baggage Demo

A practical demonstration of **OpenTelemetry Baggage** propagation across microservices in an e-commerce scenario. This demo shows how customer context (tier, promotions, region) flows through distributed services to enable dynamic pricing, inventory routing, and personalized experiences.

## 🎯 What is Baggage?

**OpenTelemetry Baggage** is a context propagation mechanism that allows you to pass key-value pairs across service boundaries. Unlike trace context (which only carries trace/span IDs), baggage can carry **business context** that influences application logic.

### Why Use Baggage?

- **Contextual Logging**: Every log automatically includes customer context
- **Business Decisions**: Services can make decisions based on propagated context
- **No Parameter Passing**: Context flows automatically through HTTP/gRPC without manual header management
- **Distributed Debugging**: Track user sessions across all services

## 🏗️ Architecture

```
Customer Request
    ↓
Storefront API (Port 5003)
    ├─ Sets baggage: customer.tier, promo.code, region, session.id
    ├─→ Pricing Service (Port 5001)
    │    └─ Reads baggage → applies dynamic pricing
    └─→ Inventory Service (Port 5002)
         └─ Reads baggage → routes to regional warehouse
```

## 📦 Baggage Items

| Key | Example | Used By | Purpose |
|-----|---------|---------|---------|
| `customer.tier` | `premium`, `regular`, `new` | Pricing, Inventory | Tier-based discounts, priority allocation |
| `promo.code` | `SUMMER25`, `LOYAL10` | Pricing | Promotional discounts |
| `region` | `us-east`, `eu-west`, `ap-south` | Inventory | Regional warehouse routing |
| `session.id` | `sess_abc123` | All services | Request correlation, debugging |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- (Optional) SigNoz account or OTLP endpoint for observability

### Installation

1. **Clone or navigate to the demo directory**:
   ```bash
   cd /Users/dhruv/code/examples/python/ecommerce-otel-baggage
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your OTLP endpoint and ingestion key
   ```

5. **Start all services**:
   ```bash
   ./run_demo.sh
   ```

   Or start services manually:
   ```bash
   # Terminal 1 - Inventory Service
   OTEL_SERVICE_NAME="inventory-service" opentelemetry-instrument python inventory_service.py

   # Terminal 2 - Pricing Service
   OTEL_SERVICE_NAME="pricing-service" opentelemetry-instrument python pricing_service.py

   # Terminal 3 - Storefront API
   OTEL_SERVICE_NAME="storefront-api" opentelemetry-instrument python storefront_api.py
   ```

## 🧪 Try the Demo

### Example 1: Premium Customer with Promo Code

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: SUMMER25" \
  -d '{
    "customer_id": "cust_premium_001",
    "product_id": "laptop_pro_15",
    "quantity": 1,
    "session_id": "sess_demo_123"
  }'
```

**What happens**:
- Storefront sets baggage: `customer.tier=premium`, `promo.code=SUMMER25`, `region=us-east`
- Pricing service reads baggage → applies 10% tier discount + 25% promo = **33.5% total discount**
- Inventory service reads baggage → routes to `WH-US-EAST-01` warehouse, **priority allocation**

**Response** (excerpt):
```json
{
  "pricing": {
    "base_price": 1299.99,
    "final_price": 865.49,
    "discount_percentage": 33.4
  },
  "inventory": {
    "warehouse": "WH-US-EAST-01",
    "allocation_type": "priority"
  }
}
```

### Example 2: Regular Customer, No Promo

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_regular_001",
    "product_id": "phone_ultra",
    "quantity": 1,
    "session_id": "sess_regular_456"
  }'
```

**What happens**:
- Baggage: `customer.tier=regular`, `region=eu-west`
- Pricing: **No discounts** applied (base price)
- Inventory: Routes to `WH-EU-WEST-01`, standard allocation

### Example 3: New Customer with Welcome Promo

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: WELCOME5" \
  -d '{
    "customer_id": "cust_new_001",
    "product_id": "tablet_mini",
    "quantity": 2,
    "session_id": "sess_new_789"
  }'
```

**What happens**:
- Baggage: `customer.tier=new`, `promo.code=WELCOME5`, `region=ap-south`
- Pricing: 5% new customer discount + 5% promo = **9.75% total discount**
- Inventory: Routes to `WH-AP-SOUTH-01`

## 📚 Available Customers & Products

### Customers

```bash
curl http://localhost:5003/customers
```

| ID | Name | Tier | Region |
|----|------|------|--------|
| `cust_premium_001` | Alice Premium | premium | us-east |
| `cust_regular_001` | Bob Regular | regular | eu-west |
| `cust_new_001` | Charlie Newbie | new | ap-south |

### Products

```bash
curl http://localhost:5003/products
```

| ID | Name | Base Price |
|----|------|------------|
| `laptop_pro_15` | Laptop Pro 15" | $1,299.99 |
| `phone_ultra` | Phone Ultra | $999.99 |
| `tablet_mini` | Tablet Mini | $399.99 |

### Promo Codes

| Code | Discount |
|------|----------|
| `SUMMER25` | 25% off |
| `LOYAL10` | 10% off |
| `WELCOME5` | 5% off |

## 🔍 How Baggage Works

### 1. Setting Baggage (Storefront API)

```python
from opentelemetry import context
from opentelemetry.baggage import set_baggage

# Create context with baggage
ctx = set_baggage("customer.tier", "premium")
ctx = set_baggage("promo.code", "SUMMER25", ctx)
ctx = set_baggage("region", "us-east", ctx)
ctx = set_baggage("session.id", "sess_123", ctx)

# Attach context
token = context.attach(ctx)

try:
    # Baggage automatically propagates in HTTP headers
    response = requests.get("http://localhost:5001/price/laptop_pro_15")
finally:
    context.detach(token)
```

### 2. Reading Baggage (Downstream Services)

```python
from opentelemetry.baggage import get_baggage

# Read individual baggage items
customer_tier = get_baggage("customer.tier")  # "premium"
promo_code = get_baggage("promo.code")        # "SUMMER25"
session_id = get_baggage("session.id")        # "sess_123"

# Use baggage in business logic
if customer_tier == "premium":
    price *= 0.90  # 10% discount
```

### 3. Automatic Propagation

OpenTelemetry's auto-instrumentation (`opentelemetry-instrumentation-requests`, `opentelemetry-instrumentation-flask`) automatically:
- Injects baggage into HTTP headers (`baggage: customer.tier=premium,promo.code=SUMMER25,...`)
- Extracts baggage from incoming requests
- Makes it available via `get_baggage()`

**No manual header management required!**

## 📊 Observability in SigNoz

When OTLP export is configured, you'll see:

1. **Traces with Baggage**: All spans include baggage as attributes
2. **Contextual Logs**: Every log has `customer.tier`, `session.id` automatically
3. **Cross-Service Correlation**: Filter all logs for `session.id=sess_123` across all 3 services
4. **Business Metrics**: Group metrics by `customer.tier`, `region`, etc.

## 🎓 Key Learning Points

### ✅ Business Logic Impact
Unlike simple correlation IDs, baggage **actively influences** business decisions:
- Pricing service uses `customer.tier` and `promo.code` to calculate prices
- Inventory service uses `region` to route to warehouses
- Premium customers get priority allocation

### ✅ Zero Boilerplate
No need to:
- Manually add headers to every HTTP call
- Pass context through function parameters
- Extract and forward headers in middleware

### ✅ Observability Benefits
- **Debugging**: "Show me all logs for session `sess_abc123`"
- **Analytics**: "How many premium customers are using promo codes?"
- **Monitoring**: "Track requests by region and tier"

## 🛠️ Project Structure

```
ecommerce-otel-baggage/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── run_demo.sh               # Start all services
├── logs/                     # Service logs
├── storefront_api.py         # Port 5003 - Sets baggage
├── pricing_service.py        # Port 5001 - Reads baggage for pricing
└── inventory_service.py      # Port 5002 - Reads baggage for warehouse routing
```

## 🔧 Configuration

### Environment Variables

```bash
# OTLP Endpoint (optional - defaults to localhost:4317)
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.in.signoz.cloud:443

# SigNoz Ingestion Key (if using SigNoz)
OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=YOUR_KEY_HERE

# Service name (set automatically by run_demo.sh)
OTEL_SERVICE_NAME=storefront-api

# Enable logging auto-instrumentation
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
```

### Running Without OTLP Export

If you don't have an OTLP endpoint, the demo still works! Just run the services and baggage will propagate. You won't see traces/metrics in an observability backend, but you'll see baggage in logs.

## 📖 Additional Resources

- [OpenTelemetry Baggage Specification](https://opentelemetry.io/docs/concepts/signals/baggage/)
- [W3C Baggage Specification](https://www.w3.org/TR/baggage/)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/languages/python/)

## 🐛 Troubleshooting

**Services won't start**:
- Ensure ports 5003, 5001, 5002 are available
- Check virtual environment is activated
- Verify Python 3.12+ is installed

**Baggage not propagating**:
- Make sure you're using `opentelemetry-instrument` to run services
- Check that `context.attach()` is called before making HTTP requests
- Verify Flask and Requests instrumentation is installed

**Can't connect to SigNoz**:
- Verify `OTEL_EXPORTER_OTLP_ENDPOINT` is correct
- Check ingestion key in `OTEL_EXPORTER_OTLP_HEADERS`
- Services work without OTLP export, just won't send telemetry

## 🎬 Demo Script

1. **Start all services**: `./run_demo.sh`
2. **Run example request**: Use the premium customer example above
3. **Check logs**: `tail -f logs/*.log` to see baggage in action
4. **View in SigNoz**: Search for `session.id=sess_demo_123` to see distributed trace
5. **Try different scenarios**: Mix different customers, products, and promo codes

## 📝 License

MIT
