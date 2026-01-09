#!/bin/bash

# Load Generator for Serilog + OpenTelemetry Demo API
# This script generates sample traffic to demonstrate tracing and logging

API_URL="${API_URL:-http://localhost:5000}"
SLEEP_TIME="${SLEEP_TIME:-2}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  Serilog + OTEL Load Generator${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo "API URL: $API_URL"
echo "Sleep between requests: ${SLEEP_TIME}s"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Function to make HTTP requests
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}→ ${description}${NC}"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${API_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${API_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed \$d)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ Status: $http_code${NC}"
    elif [ "$http_code" -ge 400 ] && [ "$http_code" -lt 600 ]; then
        echo -e "${RED}✗ Status: $http_code${NC}"
    else
        echo -e "${YELLOW}! Status: $http_code${NC}"
    fi
    
    # Show abbreviated response
    echo "$body" | jq -C '.' 2>/dev/null || echo "$body" | head -c 200
    echo ""
}

# Counter for generated data
counter=1

# Main loop
while true; do
    echo -e "${BLUE}========== Iteration $counter ==========${NC}"
    echo ""
    
    # 1. Health check
    make_request GET "/health" "" "Health Check"
    sleep "$SLEEP_TIME"
    
    # 2. Get existing data
    make_request GET "/api/data" "" "GET /api/data - Fetch all data"
    sleep "$SLEEP_TIME"
    
    # 3. Create new data
    categories=("Electronics" "Books" "Clothing" "Food" "Toys")
    names=("Widget" "Gadget" "Item" "Product" "Thing")
    
    random_category=${categories[$RANDOM % ${#categories[@]}]}
    random_name="${names[$RANDOM % ${#names[@]}]} #$counter"
    
    data="{\"name\":\"$random_name\",\"category\":\"$random_category\"}"
    make_request POST "/api/data" "$data" "POST /api/data - Create new item"
    sleep "$SLEEP_TIME"
    
    # 4. Call external service (with trace propagation)
    make_request GET "/api/external" "" "GET /api/external - External call with trace propagation"
    sleep "$SLEEP_TIME"
    
    # 5. Trigger error endpoint (occasionally)
    if [ $((counter % 5)) -eq 0 ]; then
        make_request GET "/api/error" "" "GET /api/error - Intentional error"
        sleep "$SLEEP_TIME"
    fi
    
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    counter=$((counter + 1))
    sleep 1
done
