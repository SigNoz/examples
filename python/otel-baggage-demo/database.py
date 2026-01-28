# backend service

import logging
import requests
import random

from flask import Flask, request, jsonify
from opentelemetry.baggage import set_baggage, get_baggage, get_all
import requests


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok"})

@app.route("/get-item", methods=["GET"])
def get_item():
    print("in database, received request", request.headers)
    print("baggage", get_baggage("tenant"), get_all())
    return jsonify({"item": "item1"})

if __name__ == '__main__':
    app.run(port=8890, debug=False)