#!/bin/bash

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
COLLECTOR_HOST="${1:-localhost}"
ENDPOINT="http://${COLLECTOR_HOST}:4318/v1/traces"
DURATION=30        # Run for 30 seconds
CONCURRENCY=3      # Parallel workers
MIN_SLEEP=0.1      # Sleep between requests (seconds)
MAX_SLEEP=0.5

echo "🚀 Starting Contrib Load Generator"
echo "Target:   $ENDPOINT"
echo "Duration: ${DURATION}s | Workers: ${CONCURRENCY}"
echo "------------------------------------------------"

START_TIME_GLOBAL=$(date +%s)
END_TIME_GLOBAL=$((START_TIME_GLOBAL + DURATION))

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

# Generate random Hex string (for TraceID/SpanID)
gen_hex() {
  if command -v openssl &> /dev/null; then
    openssl rand -hex $(($1 / 2))
  else
    od -vN $(($1 / 2)) -An -tx1 /dev/urandom | tr -d ' \n'
  fi
}

# Generate random integer between min and max
gen_int() {
  awk -v min=$1 -v max=$2 'BEGIN{srand(); print int(min+rand()*(max-min+1))}'
}

# -----------------------------------------------------------------------------
# WORKER LOGIC
# -----------------------------------------------------------------------------
run_worker() {
  local id=$1
  # Initialize random seed for awk inside the loop context
  
  while [ $(date +%s) -lt $END_TIME_GLOBAL ]; do
    # 1. Generate IDs
    local trace_id=$(gen_hex 32)
    local span_id=$(gen_hex 16)
    
    # 2. Randomize Duration (10ms to 2000ms)
    local duration_ms=$(gen_int 10 2000)
    local duration_ns=$((duration_ms * 1000000))
    
    # 3. Calculate Timestamps (Current time in nanoseconds)
    # Using python or perl is usually cleaner for nano-precision math, but sticking to bash/date:
    local now_s=$(date +%s)
    local start_nano="${now_s}000000000"
    local end_nano=$((start_nano + duration_ns))

    # 4. Randomize Outcome (10% fail rate)
    local rand_outcome=$(gen_int 1 100)
    local http_status=200
    local span_status=1 # OK
    local error_bool="false"
    
    if [ "$rand_outcome" -gt 90 ]; then
       http_status=500
       span_status=2 # Error
       error_bool="true"
    fi

    # 5. Randomize Method
    local methods=("GET" "POST" "PUT" "DELETE")
    local rand_idx=$(gen_int 0 3)
    local method=${methods[$rand_idx]}

    # 6. Construct JSON Payload
    local data=$(cat <<EOF
{
 "resourceSpans": [{
   "resource": {
     "attributes": [
       { "key": "service.name", "value": { "stringValue": "payment-service" } },
       { "key": "host.name", "value": { "stringValue": "worker-node-$id" } }
     ]
   },
   "scopeSpans": [{
     "scope": { "name": "load-gen-script", "version": "1.0.0" },
     "spans": [{
       "traceId": "$trace_id",
       "spanId": "$span_id",
       "name": "${method} /api/checkout",
       "kind": 2,
       "startTimeUnixNano": "$start_nano",
       "endTimeUnixNano": "$end_nano",
       "status": {
         "code": $span_status,
         "message": "Transaction processed"
       },
       "attributes": [
         { "key": "http.method", "value": { "stringValue": "$method" } },
         { "key": "http.status_code", "value": { "intValue": $http_status } },
         { "key": "http.url", "value": { "stringValue": "http://payment-service/api/checkout" } },
         { "key": "duration_ms", "value": { "intValue": $duration_ms } },
         { "key": "error", "value": { "boolValue": $error_bool } }
       ]
     }]
   }]
 }]
}
EOF
)

    # 7. Send Request
    # Capture HTTP code from curl to debug if needed, but keeping it silent for speed
    if curl -s -f -X POST "$ENDPOINT" -H "Content-Type: application/json" -d "$data" -o /dev/null; then
       if [ "$error_bool" == "true" ]; then
         printf "x" # Print x for simulated 500 error sent successfully
       else
         printf "." # Print . for success
       fi
    else
       printf "E" # Print E for network connection failure
    fi

    # 8. Random Sleep
    local sleep_time=$(awk -v min=$MIN_SLEEP -v max=$MAX_SLEEP 'BEGIN{srand(); print min+rand()*(max-min)}')
    sleep $sleep_time
  done
}

# -----------------------------------------------------------------------------
# EXECUTION
# -----------------------------------------------------------------------------

# Trap Ctrl+C (SIGINT) and Exit (SIGTERM)
# "kill 0" is a special bash command that kills every process in the current process group (all workers)
trap "kill 0" SIGINT SIGTERM EXIT

pids=""
for i in $(seq 1 $CONCURRENCY); do
  run_worker $i &
  pids="$pids $!"
done

# Wait for background processes. 
# If we hit Ctrl+C during this wait, the trap above triggers immediately.
wait

pids=""
for i in $(seq 1 $CONCURRENCY); do
  run_worker $i &
  pids="$pids $!"
done

wait $pids
echo ""
echo "------------------------------------------------"
echo "✅ Load test complete."
