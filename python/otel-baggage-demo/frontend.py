"""
Frontend Service - Web UI for the baggage demo
Port: 8888

Serves HTML page, randomly sets discount_eligible baggage,
and displays items with discounts.
"""

import logging
import random
import sys
import requests
from flask import Flask, render_template, jsonify
from opentelemetry.baggage import set_baggage
from opentelemetry import context, trace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler for local output (stderr for honcho compatibility)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(console_handler)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "frontend"})


@app.route("/", methods=["GET"])
def index():
    """
    Main page - serves HTML UI
    
    Workflow:
    1. Randomly decide if user gets discount (50% chance)
    2. Set discount_eligible baggage
    3. Call pricing to fetch items
    4. Render HTML template with results
    """
    # Randomly decide if user is eligible for discount
    discount_eligible = random.choice([True, False])
    
    logger.info(f"New visitor - discount_eligible: {discount_eligible}")
    
    # Set baggage; key-value pairs should be strings
    ctx = set_baggage("discount_eligible", str(discount_eligible).lower())
    token = context.attach(ctx)
    
    try:
        # Call pricing to get items (baggage auto-propagates)
        response = requests.get("http://localhost:8889/", timeout=5)
        data = response.json()
        
        items = data.get("items", [])
        discount_pct = data.get("discount_pct")
        if discount_pct is None:
            discount_pct = 0

        # set baggage attributes for tracing for analysis with observability backend like SigNoz
        span = trace.get_current_span()
        span.set_attribute("discount_eligible", discount_eligible)
        span.set_attribute("discount_pct", discount_pct)
        
        logger.info(f"Rendering page with {len(items)} items, discount: {discount_pct}%")
        
        # Render template
        return render_template(
            'index.html',
            items=items,
            discount_eligible=discount_eligible,
            discount_pct=discount_pct
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling pricing: {e}")
        return render_template(
            'error.html',
            error="Pricing service unavailable. Please ensure all services are running."
        ), 503
    
    finally:
        # Detach context
        context.detach(token)


if __name__ == '__main__':
    logger.info("Starting Frontend Service on port 8888")
    app.run(host='0.0.0.0', port=8888, debug=False)
