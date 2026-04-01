import requests
import time

max_calls = input("Enter max API calls to make: ")

try:
    max_calls = int(max_calls)
    assert max_calls > 0, ValueError
except Exception:
    raise ValueError("max calls must be a positive integer")

for _ in range(max_calls):
    response = requests.get("http://localhost:8085/external", timeout=10)
    print(response.json())
    time.sleep(0.3)
