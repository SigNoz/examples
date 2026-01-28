# frontend for the app

import logging
import requests
import random

import requests
from flask import Flask, request, jsonify
from opentelemetry.baggage import set_baggage, get_baggage
from opentelemetry.context import attach, detach


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# List of backend service URLs
BACKEND_SERVICES = [
    "http://localhost:8889",
    "http://localhost:8890"
]


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok"})

@app.route("/external", methods=["GET"])
def external():
    int = random.randrange(1, 10)
    ctx = set_baggage("user", "dhruv")
    ctx = set_baggage("tenant", "acme", ctx)
    ctx = set_baggage("int", int, ctx)

    token = attach(ctx)

    target_url = random.choice(BACKEND_SERVICES)
    target_url = BACKEND_SERVICES[0]

    resp = requests.get(f"{target_url}")
    print(resp.text)
    print()
    print(resp.headers)
    print()
    print(resp.request.headers)
    return jsonify({"status": "ok"})




@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    # Simple round-robin or random selection
    target_url = random.choice(BACKEND_SERVICES)
    
    # Forward the request to the backend
    try:
        response = requests.get(f"{target_url}/recommendations", headers=dict(request.headers))
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8888, debug=False)
