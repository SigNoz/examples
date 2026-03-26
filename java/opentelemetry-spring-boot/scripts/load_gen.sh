#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8085}"
SLEEP_TIME="${SLEEP_TIME:-1}"
FIBONACCI_BATCH_SIZE="${FIBONACCI_BATCH_SIZE:-5}"
VALID_INPUTS=(0 1 2 3 5 8 13 21 34 55 61 89 92)
INVALID_INPUTS=(-1 93 128 200 256)

while true; do
  echo "$(date +'%T') - Root: Sending 2 requests (timeout 2s)"
  curl -s --max-time 2 "${BASE_URL}/" > /dev/null &
  curl -s --max-time 2 "${BASE_URL}/invalid" > /dev/null &

  echo "$(date +'%T') - Fibonacci: Sending ${FIBONACCI_BATCH_SIZE} valid requests"
  for (( i = 0; i < FIBONACCI_BATCH_SIZE; i++ )); do
    VALID_INDEX=$(( RANDOM % ${#VALID_INPUTS[@]} ))
    VALID_VAL="${VALID_INPUTS[$VALID_INDEX]}"
    curl -s --max-time 5 \
      -H "Content-Type: application/json" \
      -d "{\"number\": ${VALID_VAL}}" \
      "${BASE_URL}/fibonacci" > /dev/null &
  done

  if (( RANDOM % 4 == 0 )); then
    INVALID_INDEX=$(( RANDOM % ${#INVALID_INPUTS[@]} ))
    INVALID_VAL="${INVALID_INPUTS[$INVALID_INDEX]}"
    echo "$(date +'%T') - Fibonacci: Sending invalid request with n=${INVALID_VAL} (expect 422)"
    curl -s --max-time 5 \
      -H "Content-Type: application/json" \
      -d "{\"number\": ${INVALID_VAL}}" \
      "${BASE_URL}/fibonacci" > /dev/null &
  fi

  echo "$(date +'%T') - Sleeping for ${SLEEP_TIME} seconds..."
  sleep "${SLEEP_TIME}"
done
