#!/bin/bash

while true; do
  # Call root endpoints
  echo "$(date +'%T') - Root: Sending 2 requests (timeout 2s)"
  curl -s --max-time 2 "http://localhost:8085/" > /dev/null &
  curl -s --max-time 2 "http://localhost:8085//" > /dev/null &
  
  # Call fibonacci with a random value between 0 and 20
  # Note: The server uses a recursive implementation, so higher values will be slow.
  # Also, the server expects JSON format: {"number": VAL}
  VAL=$(( RANDOM % 21 ))
  echo "$(date +'%T') - Fibonacci: Sending request with n=$VAL"
  curl -s --max-time 5 \
       -H "Content-Type: application/json" \
       -d "{\"number\": $VAL}" \
       "http://localhost:8085/fibonacci" > /dev/null &

  # Random pause to continuously generate load
  SLEEP_TIME=1
  echo "$(date +'%T') - Sleeping for $SLEEP_TIME seconds..."
  sleep $SLEEP_TIME
done
