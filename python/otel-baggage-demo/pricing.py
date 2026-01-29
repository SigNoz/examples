"""
Pricing Service - Middleware that calculates discount percentage
Port: 8889

Reads discount_eligible from baggage, calculates discount %, 
adds it to baggage, and calls processor.
"""

import logging
import random
import sys
import requests
from flask import Flask, request, jsonify
from opentelemetry.baggage import get_baggage, set_baggage
from opentelemetry import context

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler for local output (stderr for honcho compatibility)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(console_handler)

app = Flask(__name__)

# Possible discount percentages
DISCOUNT_OPTIONS = [10, 15, 20, 25]


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "pricing"})


@app.route("/", methods=["GET"])
def get_items():
    """
    Fetch items from processor
    
    Workflow:
    1. Read discount_eligible from baggage
    2. If eligible, randomly calculate discount %
    3. Add discount_pct to baggage
    4. Call processor to get items
    5. Return items + discount info
    """
    # Read baggage set by frontend
    discount_eligible = get_baggage("discount_eligible")
    
    logger.info(f"Pricing received request - discount_eligible: {discount_eligible}")
    
    # If user is eligible, calculate discount percentage
    discount_pct = None
    if discount_eligible == "true":
        discount_pct = random.choice(DISCOUNT_OPTIONS)
        logger.info(f"User is eligible! Calculated discount: {discount_pct}%")
        
        # Add discount percentage to baggage
        ctx = set_baggage("discount_pct", str(discount_pct))
        token = context.attach(ctx)
    else:
        logger.info("User is not eligible for discount")
        token = None
    
    try:
        # Call processor to get items (baggage auto-propagates)
        response = requests.get("http://localhost:8890/get-items", timeout=5)
        data = response.json()
        
        logger.info(f"Received {len(data.get('items', []))} items from processor")
        
        # Add discount info to response
        result = {
            "items": data.get("items", []),
            "discount_eligible": discount_eligible == "true",
            "discount_pct": discount_pct,
            "message": f"You got {discount_pct}% off!" if discount_pct else "No discount this time"
        }
        
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling processor: {e}")
        return jsonify({"error": "Service unavailable"}), 503
    
    finally:
        # Detach context
        if token:
            context.detach(token)


if __name__ == '__main__':
    logger.info("Starting Pricing Service on port 8889")
    app.run(host='0.0.0.0', port=8889, debug=False)
