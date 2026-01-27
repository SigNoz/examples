# Example Requests for E-Commerce Baggage Demo

This file contains various curl commands to test different baggage propagation scenarios.

## Prerequisites

Ensure all three services are running:
```bash
./run_demo.sh
```

---

## Scenario 1: Premium Customer with Maximum Discounts

**Customer**: Alice Premium (tier: premium, region: us-east)  
**Product**: Laptop Pro 15" ($1,299.99)  
**Promo**: SUMMER25 (25% off)

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: SUMMER25" \
  -d '{
    "customer_id": "cust_premium_001",
    "product_id": "laptop_pro_15",
    "quantity": 1,
    "session_id": "sess_premium_summer"
  }' | jq
```

**Expected Discounts**:
- Premium tier: 10% off
- SUMMER25 promo: 25% off
- **Total discount: 33.4%** ($1,299.99 → $865.49)

**Baggage Set**:
- `customer.tier=premium`
- `promo.code=SUMMER25`
- `region=us-east`
- `session.id=sess_premium_summer`

---

## Scenario 2: Regular Customer, No Promotion

**Customer**: Bob Regular (tier: regular, region: eu-west)  
**Product**: Phone Ultra ($999.99)  
**Promo**: None

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_regular_001",
    "product_id": "phone_ultra",
    "quantity": 1,
    "session_id": "sess_regular_nopromo"
  }' | jq
```

**Expected Discounts**: None (pays full price)

**Baggage Set**:
- `customer.tier=regular`
- `promo.code=` (empty)
- `region=eu-west`
- `session.id=sess_regular_nopromo`

---

## Scenario 3: New Customer Welcome Offer

**Customer**: Charlie Newbie (tier: new, region: ap-south)  
**Product**: Tablet Mini ($399.99)  
**Promo**: WELCOME5 (5% off)

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: WELCOME5" \
  -d '{
    "customer_id": "cust_new_001",
    "product_id": "tablet_mini",
    "quantity": 2,
    "session_id": "sess_new_welcome"
  }' | jq
```

**Expected Discounts**:
- New customer: 5% off
- WELCOME5 promo: 5% off
- **Total discount: 9.75%** ($399.99 → $361.00 per unit)

**Baggage Set**:
- `customer.tier=new`
- `promo.code=WELCOME5`
- `region=ap-south`
- `session.id=sess_new_welcome`

---

## Scenario 4: Loyalty Program (Regular Customer)

**Customer**: Bob Regular (tier: regular, region: eu-west)  
**Product**: Laptop Pro 15" ($1,299.99)  
**Promo**: LOYAL10 (10% off)

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: LOYAL10" \
  -d '{
    "customer_id": "cust_regular_001",
    "product_id": "laptop_pro_15",
    "quantity": 1,
    "session_id": "sess_regular_loyal"
  }' | jq
```

**Expected Discounts**:
- Regular tier: 0% (no tier discount)
- LOYAL10 promo: 10% off
- **Total discount: 10%** ($1,299.99 → $1,169.99)

**Baggage Set**:
- `customer.tier=regular`
- `promo.code=LOYAL10`
- `region=eu-west`
- `session.id=sess_regular_loyal`

---

## Scenario 5: Invalid Promo Code

**Customer**: Alice Premium (tier: premium, region: us-east)  
**Product**: Phone Ultra ($999.99)  
**Promo**: INVALID (should be ignored)

```bash
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: INVALID" \
  -d '{
    "customer_id": "cust_premium_001",
    "product_id": "phone_ultra",
    "quantity": 1,
    "session_id": "sess_invalid_promo"
  }' | jq
```

**Expected Discounts**:
- Premium tier: 10% off
- INVALID promo: ignored
- **Total discount: 10%** ($999.99 → $899.99)

**Baggage Set**:
- `customer.tier=premium`
- `promo.code=INVALID` (set but not used by pricing service)
- `region=us-east`
- `session.id=sess_invalid_promo`

---

## Utility Endpoints

### List All Customers
```bash
curl http://localhost:5003/customers | jq
```

### List All Products
```bash
curl http://localhost:5003/products | jq
```

### Check Service Health
```bash
# Storefront
curl http://localhost:5003/health | jq

# Pricing
curl http://localhost:5001/health | jq

# Inventory
curl http://localhost:5002/health | jq
```

### Get Product Catalog (Base Prices)
```bash
curl http://localhost:5001/catalog | jq
```

### View Full Inventory
```bash
curl http://localhost:5002/inventory | jq
```

### View Warehouse Mapping
```bash
curl http://localhost:5002/warehouses | jq
```

---

## Observing Baggage in Logs

After making requests, check the logs to see baggage in action:

```bash
# View all logs
tail -f logs/*.log

# View specific service logs
tail -f logs/storefront.log
tail -f logs/pricing.log
tail -f logs/inventory.log

# Search for a specific session
grep "sess_premium_summer" logs/*.log
```

You should see log entries that include:
- `tier=premium`
- `promo=SUMMER25`
- `region=us-east`
- `session=sess_premium_summer`

---

## Testing Baggage Propagation

To verify baggage is propagating correctly:

1. **Make a request** with a unique session ID
2. **Search logs** for that session ID across all services
3. **Verify** that all three services log the same baggage values

Example:
```bash
# Make request
curl -X POST http://localhost:5003/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Promo-Code: SUMMER25" \
  -d '{
    "customer_id": "cust_premium_001",
    "product_id": "laptop_pro_15",
    "quantity": 1,
    "session_id": "TEST_SESSION_999"
  }'

# Check logs (after 1-2 seconds)
grep "TEST_SESSION_999" logs/*.log
```

You should see the session ID appear in logs from all three services!
