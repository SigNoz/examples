# backend service

import logging
import requests
import random

from flask import Flask, request, jsonify
from opentelemetry.baggage import set_baggage, get_baggage
import requests


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    print("received request, parsing headers")
    print(request.headers)

    response = requests.get("http://localhost:8890/get-item")
    print("got resp from db", response.json(), response.headers)
    print("request headers", response.request.headers)

    return jsonify({"status": "ok"})



if __name__ == '__main__':
    app.run(port=8889, debug=False)
