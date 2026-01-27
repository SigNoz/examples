"""
Storefront API - Customer-facing e-commerce service
Port: 5003

This service receives customer requests, sets baggage with customer context,
and calls downstream services (pricing and inventory).
"""

import logging
import requests
from flask import Flask, request, jsonify
from opentelemetry import context
from opentelemetry.baggage import set_baggage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock customer database
CUSTOMERS = {
    "cust_premium_001": {
        "id": "cust_premium_001",
        "name": "Alice Premium",
        "tier": "premium",
        "region": "us-east"
    },
    "cust_regular_001": {
        "id": "cust_regular_001",
        "name": "Bob Regular",
        "tier": "regular",
        "region": "eu-west"
    },
    "cust_new_001": {
        "id": "cust_new_001",
        "name": "Charlie Newbie",
        "tier": "new",
        "region": "ap-south"
    }
}

# Mock product catalog
PRODUCTS = {
    "laptop_pro_15": {"name": "Laptop Pro 15\"", "base_price": 1299.99},
    "phone_ultra": {"name": "Phone Ultra", "base_price": 999.99},
    "tablet_mini": {"name": "Tablet Mini", "base_price": 399.99}
}


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "storefront-api"})


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    """
    Add item to shopping cart
    
    This endpoint:
    1. Looks up customer information
    2. Sets baggage with customer context
    3. Calls pricing and inventory services
    4. Returns cart information with final price
    """
    data = request.json
    customer_id = data.get("customer_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    session_id = data.get("session_id", "sess_default")
    
    # Get promo code from header
    promo_code = request.headers.get("X-Promo-Code", "")
    
    # Validate inputs
    if not customer_id or not product_id:
        return jsonify({"error": "customer_id and product_id required"}), 400
    
    # Look up customer
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    # Validate product
    if product_id not in PRODUCTS:
        return jsonify({"error": "Product not found"}), 404
    
    logger.info(f"Processing cart request for customer {customer_id}, product {product_id}")
    
    # ===== BAGGAGE PROPAGATION STARTS HERE =====
    # Set baggage with customer context
    ctx = set_baggage("customer.tier", customer["tier"])
    ctx = set_baggage("promo.code", promo_code, ctx)
    ctx = set_baggage("region", customer["region"], ctx)
    ctx = set_baggage("session.id", session_id, ctx)
    
    logger.info(f"Set baggage: tier={customer['tier']}, promo={promo_code}, region={customer['region']}, session={session_id}")
    
    # Attach the context so baggage propagates to downstream calls
    token = context.attach(ctx)
    
    try:
        # Call pricing service - baggage automatically propagates via HTTP headers
        pricing_response = requests.get(
            f"http://localhost:5001/price/{product_id}",
            timeout=5
        )
        pricing_data = pricing_response.json()
        
        # Call inventory service - baggage automatically propagates
        inventory_response = requests.get(
            f"http://localhost:5002/stock/{product_id}",
            params={"quantity": quantity},
            timeout=5
        )
        inventory_data = inventory_response.json()
        
        # Calculate total
        unit_price = pricing_data["final_price"]
        total = unit_price * quantity
        
        logger.info(f"Cart total: ${total:.2f} for {quantity}x {product_id}")
        
        # Build response
        response = {
            "success": True,
            "customer": {
                "id": customer_id,
                "name": customer["name"],
                "tier": customer["tier"]
            },
            "product": {
                "id": product_id,
                "name": PRODUCTS[product_id]["name"],
                "quantity": quantity
            },
            "pricing": pricing_data,
            "inventory": inventory_data,
            "cart": {
                "session_id": session_id,
                "unit_price": unit_price,
                "quantity": quantity,
                "total": round(total, 2)
            },
            "baggage_info": {
                "note": "Baggage was set and propagated to downstream services",
                "items": {
                    "customer.tier": customer["tier"],
                    "promo.code": promo_code,
                    "region": customer["region"],
                    "session.id": session_id
                }
            }
        }
        
        return jsonify(response)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling downstream service: {e}")
        return jsonify({"error": "Service unavailable", "details": str(e)}), 503
    
    finally:
        # Always detach context to avoid leaking
        context.detach(token)


@app.route("/customers", methods=["GET"])
def list_customers():
    """List available customers for demo purposes"""
    return jsonify({"customers": list(CUSTOMERS.values())})


@app.route("/products", methods=["GET"])
def list_products():
    """List available products for demo purposes"""
    products_list = [
        {"id": k, **v} for k, v in PRODUCTS.items()
    ]
    return jsonify({"products": products_list})


if __name__ == "__main__":
    logger.info("Starting Storefront API on port 5003")
    app.run(host="0.0.0.0", port=5003, debug=False)
