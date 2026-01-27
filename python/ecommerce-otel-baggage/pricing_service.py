"""
Pricing Service - Dynamic pricing based on customer tier and promotions
Port: 5001

This service reads baggage to apply:
- Tier-based discounts (premium, regular, new)
- Promotional codes
"""

import logging
from flask import Flask, jsonify
from opentelemetry.baggage import get_baggage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Base product prices
CATALOG = {
    "laptop_pro_15": {"name": "Laptop Pro 15\"", "price": 1299.99},
    "phone_ultra": {"name": "Phone Ultra", "price": 999.99},
    "tablet_mini": {"name": "Tablet Mini", "price": 399.99}
}

# Promotional codes
PROMO_CODES = {
    "SUMMER25": 0.75,   # 25% off
    "LOYAL10": 0.90,    # 10% off
    "WELCOME5": 0.95    # 5% off
}


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "pricing-service"})


@app.route("/price/<product_id>", methods=["GET"])
def get_price(product_id):
    """
    Calculate dynamic price for a product
    
    Uses baggage to determine:
    - Customer tier (premium/regular/new) → tier discount
    - Promo code → promotional discount
    - Session ID → for logging/debugging
    """
    
    # ===== READING BAGGAGE =====
    customer_tier = get_baggage("customer.tier") or "regular"
    promo_code = get_baggage("promo.code") or ""
    session_id = get_baggage("session.id") or "unknown"
    
    logger.info(f"[{session_id}] Pricing request for {product_id} - tier={customer_tier}, promo={promo_code}")
    
    # Validate product
    if product_id not in CATALOG:
        logger.warning(f"[{session_id}] Product not found: {product_id}")
        return jsonify({"error": "Product not found"}), 404
    
    # Get base price
    base_price = CATALOG[product_id]["price"]
    price = base_price
    discounts_applied = []
    
    # Apply tier-based discount
    tier_discount = 0.0
    if customer_tier == "premium":
        tier_discount = 0.10  # 10% off
        price *= 0.90
        discounts_applied.append(f"Premium tier: 10% off")
    elif customer_tier == "new":
        tier_discount = 0.05  # 5% off for new customers
        price *= 0.95
        discounts_applied.append(f"New customer: 5% off")
    
    # Apply promo code
    promo_discount = 0.0
    if promo_code and promo_code in PROMO_CODES:
        multiplier = PROMO_CODES[promo_code]
        promo_discount = 1.0 - multiplier
        price *= multiplier
        discounts_applied.append(f"Promo {promo_code}: {int(promo_discount * 100)}% off")
    elif promo_code:
        logger.warning(f"[{session_id}] Invalid promo code: {promo_code}")
    
    # Calculate total discount
    total_discount = base_price - price
    discount_percentage = (total_discount / base_price) * 100 if base_price > 0 else 0
    
    logger.info(
        f"[{session_id}] Price calculated: ${price:.2f} "
        f"(base: ${base_price:.2f}, discount: {discount_percentage:.1f}%)"
    )
    
    response = {
        "product_id": product_id,
        "product_name": CATALOG[product_id]["name"],
        "base_price": round(base_price, 2),
        "final_price": round(price, 2),
        "discount_amount": round(total_discount, 2),
        "discount_percentage": round(discount_percentage, 1),
        "discounts_applied": discounts_applied,
        "pricing_factors": {
            "customer_tier": customer_tier,
            "tier_discount": f"{int(tier_discount * 100)}%",
            "promo_code": promo_code if promo_code else "none",
            "promo_discount": f"{int(promo_discount * 100)}%" if promo_code else "0%"
        },
        "session_id": session_id
    }
    
    return jsonify(response)


@app.route("/catalog", methods=["GET"])
def get_catalog():
    """Get product catalog with base prices"""
    return jsonify({"catalog": CATALOG})


if __name__ == "__main__":
    logger.info("Starting Pricing Service on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
