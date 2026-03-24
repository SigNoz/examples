#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8085}"
SLEEP_TIME="${SLEEP_TIME:-1}"

while true; do
  echo "$(date +'%T') - Root: Sending 2 requests (timeout 2s)"
  curl -s --max-time 2 "${BASE_URL}/" > /dev/null &
  curl -s --max-time 2 "${BASE_URL}//" > /dev/null &

  VAL=$(( RANDOM % 21 ))
  echo "$(date +'%T') - Fibonacci: Sending request with n=$VAL"
  curl -s --max-time 5 \
    -H "Content-Type: application/json" \
    -d "{\"number\": $VAL}" \
    "${BASE_URL}/fibonacci" > /dev/null &

  echo "$(date +'%T') - Sleeping for ${SLEEP_TIME} seconds..."
  sleep "${SLEEP_TIME}"
done
