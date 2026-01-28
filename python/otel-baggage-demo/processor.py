"""
Processor Service - Pricing logic with baggage-based discounts
Port: 8890

Reads baggage to apply discounts to item prices.
Returns both original and discounted prices.
"""

import logging
from flask import Flask, request, jsonify
from opentelemetry.baggage import get_baggage, get_all

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock items database
ITEMS = [
    {"id": 1, "name": "Premium Coffee Mug", "price": 24.99},
    {"id": 2, "name": "Ergonomic Mouse Pad", "price": 18.99},
    {"id": 3, "name": "Laptop Stand", "price": 49.99},
    {"id": 4, "name": "Wireless Keyboard", "price": 79.99},
]


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "processor"})


@app.route("/get-items", methods=["GET"])
def get_items():
    """
    Get items with pricing based on baggage context
    
    Reads baggage:
    - discount_eligible: Whether user gets discount
    - discount_pct: Discount percentage to apply
    
    Returns both original and discounted prices
    """
    # Read baggage
    discount_eligible = get_baggage("discount_eligible")
    discount_pct = get_baggage("discount_pct")
    all_baggage = get_all()
    
    logger.info(f"Processing items - Baggage: {all_baggage}")
    logger.info(f"Discount eligible: {discount_eligible}, Discount %: {discount_pct}")
    
    # Process items
    processed_items = []
    for item in ITEMS:
        original_price = item["price"]
        discounted_price = original_price
        
        # Apply discount if eligible
        if discount_eligible == "true" and discount_pct:
            try:
                discount_decimal = float(discount_pct) / 100
                discounted_price = original_price * (1 - discount_decimal)
            except (ValueError, TypeError):
                logger.warning(f"Invalid discount_pct: {discount_pct}")
        
        processed_items.append({
            "id": item["id"],
            "name": item["name"],
            "original_price": round(original_price, 2),
            "discounted_price": round(discounted_price, 2),
            "has_discount": discount_eligible == "true" and original_price != discounted_price
        })
    
    logger.info(f"Returning {len(processed_items)} items")
    
    return jsonify({
        "items": processed_items,
        "discount_applied": discount_eligible == "true",
        "discount_pct": discount_pct if discount_eligible == "true" else None
    })


if __name__ == '__main__':
    logger.info("Starting Processor Service on port 8890")
    app.run(host='0.0.0.0', port=8890, debug=False)