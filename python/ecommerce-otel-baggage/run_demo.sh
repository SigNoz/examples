#!/bin/bash

# E-Commerce OpenTelemetry Baggage Demo - Run Script
# This script starts all three services with auto-instrumentation

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  E-Commerce OTel Baggage Demo${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q -r requirements.txt

echo ""
echo -e "${BLUE}Starting services with OpenTelemetry auto-instrumentation...${NC}"
echo ""

# Start Inventory Service (Port 5002)
echo -e "${GREEN}[1/3] Starting Inventory Service on port 5002...${NC}"
OTEL_SERVICE_NAME="inventory-service" \
opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    python inventory_service.py > logs/inventory.log 2>&1 &
INVENTORY_PID=$!
echo "  PID: $INVENTORY_PID"

sleep 2

# Start Pricing Service (Port 5001)
echo -e "${GREEN}[2/3] Starting Pricing Service on port 5001...${NC}"
OTEL_SERVICE_NAME="pricing-service" \
opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    python pricing_service.py > logs/pricing.log 2>&1 &
PRICING_PID=$!
echo "  PID: $PRICING_PID"

sleep 2

# Start Storefront API (Port 5003)
echo -e "${GREEN}[3/3] Starting Storefront API on port 5003...${NC}"
OTEL_SERVICE_NAME="storefront-api" \
opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    python storefront_api.py > logs/storefront.log 2>&1 &
STOREFRONT_PID=$!
echo "  PID: $STOREFRONT_PID"

sleep 3

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}All services started successfully!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo "Service URLs:"
echo "  - Storefront API:    http://localhost:5003"
echo "  - Pricing Service:   http://localhost:5001"
echo "  - Inventory Service: http://localhost:5002"
echo ""
echo "Process IDs:"
echo "  - Storefront API:    $STOREFRONT_PID"
echo "  - Pricing Service:   $PRICING_PID"
echo "  - Inventory Service: $INVENTORY_PID"
echo ""
echo "Logs available in:"
echo "  - logs/storefront.log"
echo "  - logs/pricing.log"
echo "  - logs/inventory.log"
echo ""
echo -e "${YELLOW}To stop all services, run:${NC}"
echo "  kill $STOREFRONT_PID $PRICING_PID $INVENTORY_PID"
echo ""
echo -e "${YELLOW}Try the demo with:${NC}"
echo '  curl -X POST http://localhost:5003/cart/add \'
echo '    -H "Content-Type: application/json" \'
echo '    -H "X-Promo-Code: SUMMER25" \'
echo "    -d '{\"customer_id\": \"cust_premium_001\", \"product_id\": \"laptop_pro_15\", \"quantity\": 1, \"session_id\": \"sess_demo_123\"}'"
echo ""

# Save PIDs to file for easy cleanup
echo "$STOREFRONT_PID $PRICING_PID $INVENTORY_PID" > .demo_pids

# Wait for Ctrl+C
echo -e "${GREEN}Press Ctrl+C to stop all services...${NC}"
trap "kill $STOREFRONT_PID $PRICING_PID $INVENTORY_PID 2>/dev/null; echo ''; echo 'Services stopped.'; exit" INT
wait
