# Simplified OpenTelemetry Baggage Demo

A simple, visual demonstration of **OpenTelemetry Baggage** propagation across 3 microservices with an elegant HTML UI.

## 🎯 What This Demo Shows

- **Baggage Propagation**: See how context flows automatically through HTTP requests
- **Dynamic Pricing**: Random discount eligibility affects item prices across services
- **Visual Feedback**: Beautiful HTML UI shows discounted prices with strikethrough
- **Real Business Logic**: Baggage actively influences pricing decisions

## 🏗️ Architecture

```
Browser
   ↓
Frontend (8888) → Sets discount_eligible baggage randomly
   ↓
Backend (8889) → Calculates discount %, adds to baggage
   ↓
Processor (8890) → Reads baggage, applies discount to prices
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/dhruv/code/examples/python/otel-baggage-demo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Services (3 terminals)

**Terminal 1 - Processor:**
```bash
source venv/bin/activate
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
OTEL_SERVICE_NAME=processor opentelemetry-instrument python processor.py
```

**Terminal 2 - Backend:**
```bash
source venv/bin/activate
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
OTEL_SERVICE_NAME=backend opentelemetry-instrument python backend.py
```

**Terminal 3 - Frontend:**
```bash
source venv/bin/activate
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
OTEL_SERVICE_NAME=frontend opentelemetry-instrument python frontend.py
```

### 3. Visit the Demo

Open your browser: **http://localhost:8888**

Refresh the page multiple times to see:
- 🎉 **Sometimes**: "You're a Lucky Shopper! You got 15% off!"
- ❌ **Sometimes**: No discount (regular prices)

## 📦 Baggage Flow

| Service | Baggage Action | Key | Value | Purpose |
|---------|---------------|-----|-------|---------|
| **Frontend** | Sets | `discount_eligible` | `true`/`false` | Random 50% chance |
| **Backend** | Adds | `discount_pct` | `10`/`15`/`20`/`25` | Calculated discount |
| **Processor** | Reads | Both | - | Applies discount to prices |

## 🎨 UI Features

- **Gradient background** with purple theme
- **Discount banner** when eligible (animated slide-in)
- **Item cards** with hover effects
- **Strikethrough prices** showing original + discounted
- **Discount badges** indicating savings
- **Refresh button** to try luck again

## 🧪 What to Observe

1. **Random Discounts**: Each page reload = new random eligibility
2. **Price Changes**: Items show both original (strikethrough) and discounted prices
3. **Baggage Info**: Footer shows current baggage values
4. **Logs**: Check terminal logs to see baggage propagating

## 📝 Key Learning Points

✅ **Setting Baggage** - Frontend sets initial context  
✅ **Adding to Baggage** - Backend enriches context  
✅ **Reading Baggage** - Processor acts on context  
✅ **Auto-Propagation** - No manual header management  
✅ **Business Impact** - Pricing changes based on baggage

## 🔧 Python 3.14 Note

If using Python 3.14, set this before running services:
```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```

This fixes the protobuf compatibility issue.

## 📂 Project Structure

```
otel-baggage-demo/
├── frontend.py           # Port 8888 - HTML UI
├── backend.py        # Port 8889 - Middleware
├── processor.py          # Port 8890 - Pricing logic
├── templates/
│   └── index.html       # Elegant HTML template
└── requirements.txt
```

## 🎬 Demo Flow

1. User visits `http://localhost:8888`
2. Frontend randomly sets `discount_eligible=true/false` baggage
3. Frontend calls Backend
4. Backend reads baggage, calculates discount % if eligible
5. Backend adds `discount_pct` to baggage
6. Backend calls Processor
7. Processor reads both baggage values, applies discount
8. Processor returns items with original + discounted prices
9. Response flows back to Frontend
10. Frontend renders beautiful HTML showing results!

Enjoy! 🎉
