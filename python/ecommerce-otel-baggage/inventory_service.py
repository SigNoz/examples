"""
Inventory Service - Stock management with regional warehouses
Port: 5002

This service reads baggage to:
- Route to correct regional warehouse
- Provide priority allocation for premium customers
"""

import logging
from flask import Flask, request, jsonify
from opentelemetry.baggage import get_baggage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Regional warehouse mapping
WAREHOUSE_MAPPING = {
    "us-east": "WH-US-EAST-01",
    "us-west": "WH-US-WEST-01",
    "eu-west": "WH-EU-WEST-01",
    "ap-south": "WH-AP-SOUTH-01"
}

# Mock inventory data per warehouse
INVENTORY = {
    "WH-US-EAST-01": {
        "laptop_pro_15": {"available": 45, "reserved": 5},
        "phone_ultra": {"available": 120, "reserved": 10},
        "tablet_mini": {"available": 80, "reserved": 5}
    },
    "WH-EU-WEST-01": {
        "laptop_pro_15": {"available": 30, "reserved": 2},
        "phone_ultra": {"available": 95, "reserved": 5},
        "tablet_mini": {"available": 60, "reserved": 3}
    },
    "WH-AP-SOUTH-01": {
        "laptop_pro_15": {"available": 20, "reserved": 1},
        "phone_ultra": {"available": 70, "reserved": 4},
        "tablet_mini": {"available": 50, "reserved": 2}
    },
    "WH-US-WEST-01": {
        "laptop_pro_15": {"available": 35, "reserved": 3},
        "phone_ultra": {"available": 100, "reserved": 8},
        "tablet_mini": {"available": 65, "reserved": 4}
    }
}


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "inventory-service"})


@app.route("/stock/<product_id>", methods=["GET"])
def check_stock(product_id):
    """
    Check stock availability for a product
    
    Uses baggage to:
    - Determine regional warehouse (from region)
    - Apply priority allocation (from customer.tier)
    - Track session for debugging
    """
    
    # Get requested quantity
    quantity = int(request.args.get("quantity", 1))
    
    # ===== READING BAGGAGE =====
    customer_tier = get_baggage("customer.tier") or "regular"
    region = get_baggage("region") or "us-east"
    session_id = get_baggage("session.id") or "unknown"
    
    logger.info(
        f"[{session_id}] Stock check for {product_id} - "
        f"quantity={quantity}, region={region}, tier={customer_tier}"
    )
    
    # Determine warehouse based on region
    warehouse = WAREHOUSE_MAPPING.get(region, "WH-US-EAST-01")
    logger.info(f"[{session_id}] Routing to warehouse: {warehouse}")
    
    # Check if warehouse has the product
    if warehouse not in INVENTORY or product_id not in INVENTORY[warehouse]:
        logger.warning(f"[{session_id}] Product not found in warehouse {warehouse}")
        return jsonify({
            "error": "Product not available in this region",
            "product_id": product_id,
            "region": region,
            "warehouse": warehouse
        }), 404
    
    # Get stock info
    stock_info = INVENTORY[warehouse][product_id]
    available = stock_info["available"]
    reserved = stock_info["reserved"]
    
    # Check availability
    in_stock = available >= quantity
    can_fulfill = available >= quantity
    
    # Priority allocation for premium customers
    priority_allocated = False
    if customer_tier == "premium" and in_stock:
        priority_allocated = True
        logger.info(
            f"[{session_id}] Priority allocation for premium customer - "
            f"reserving {quantity} units"
        )
    
    # Build response
    response = {
        "product_id": product_id,
        "warehouse": warehouse,
        "region": region,
        "available_quantity": available,
        "reserved_quantity": reserved,
        "requested_quantity": quantity,
        "in_stock": in_stock,
        "can_fulfill": can_fulfill,
        "allocation": {
            "customer_tier": customer_tier,
            "priority_allocated": priority_allocated,
            "allocation_type": "priority" if priority_allocated else "standard"
        },
        "session_id": session_id,
        "status": "available" if in_stock else "out_of_stock"
    }
    
    if not in_stock:
        response["message"] = f"Insufficient stock. Available: {available}, Requested: {quantity}"
        logger.warning(f"[{session_id}] Insufficient stock for {product_id}")
    else:
        response["message"] = "Product available"
        logger.info(f"[{session_id}] Stock confirmed for {product_id}")
    
    return jsonify(response)


@app.route("/inventory", methods=["GET"])
def get_full_inventory():
    """Get full inventory across all warehouses (for demo purposes)"""
    return jsonify({"warehouses": INVENTORY})


@app.route("/warehouses", methods=["GET"])
def get_warehouses():
    """Get warehouse mapping (for demo purposes)"""
    return jsonify({"warehouse_mapping": WAREHOUSE_MAPPING})


if __name__ == "__main__":
    logger.info("Starting Inventory Service on port 5002")
    app.run(host="0.0.0.0", port=5002, debug=False)
