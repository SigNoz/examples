# Cassandra Metrics Testing Script

A Python script to generate workload and test Cassandra monitoring metrics.

> 📚 **Full Guide:** For a complete guide on Cassandra monitoring, check out the blog post: [Cassandra Monitoring with OpenTelemetry and SigNoz](https://signoz.io/guides/cassandra-monitoring/)

This script generates controlled workload against a Cassandra cluster to verify that all monitored metrics are being collected correctly by OpenTelemetry and sent to SigNoz.

## 📊 Metrics Tested

| Metric | Test | What It Does |
|--------|------|--------------|
| `cassandra.client.request.count` | requests | Generates read/write operations |
| `cassandra.client.request.latency` | requests | Measures operation duration |
| `cassandra.storage.load` | storage | Inserts ~30MB of data |
| `cassandra.compaction.tasks.pending` | compaction | Creates multiple SSTables |
| `jvm.memory.heap.used` | jvm | Creates memory pressure |
| `jvm.gc.collections.count` | jvm | Triggers garbage collection |
| `jvm.gc.collections.elapsed` | jvm | Measures GC duration |

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip3 install cassandra-driver
```

### Run All Tests

```bash
python3 test_metrics.py --test all
```

### Run Specific Tests

```bash
# Test request count and latency
python3 test_metrics.py --test requests

# Test storage load
python3 test_metrics.py --test storage

# Test compaction
python3 test_metrics.py --test compaction

# Test JVM/GC metrics
python3 test_metrics.py --test jvm
```

## 📋 Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | localhost | Cassandra host address |
| `--port` | 9042 | Cassandra CQL port |
| `--test` | all | Test to run: `all`, `requests`, `storage`, `compaction`, `jvm` |

### Examples

```bash
# Connect to remote Cassandra
python3 test_metrics.py --host 192.168.1.100 --port 9042 --test all

# Run only request test on localhost
python3 test_metrics.py --test requests
```

## 🧪 Test Details

### Test 1: Request Count & Latency (`--test requests`)
- **Operations:** 2,000 (1,000 writes + 1,000 reads)
- **Duration:** ~30 seconds
- **Metrics affected:** `cassandra.client.request.count`, `cassandra.client.request.latency`

### Test 2: Storage Load (`--test storage`)
- **Records:** 3,000 records × 10KB each
- **Total data:** ~30MB
- **Duration:** ~1-2 minutes
- **Metrics affected:** `cassandra.storage.load`

### Test 3: Compaction (`--test compaction`)
- **Batches:** 5 batches × 500 records
- **Duration:** ~30 seconds
- **Metrics affected:** `cassandra.compaction.tasks.pending`

### Test 4: JVM Memory & GC (`--test jvm`)
- **Operations:** 5,000 large inserts
- **Duration:** ~1-2 minutes
- **Metrics affected:** `jvm.memory.heap.used`, `jvm.gc.collections.count`, `jvm.gc.collections.elapsed`

## 📈 Expected Output

```
################################################################################
# CASSANDRA METRICS TESTING SUITE
# Starting at: 2026-01-10 15:00:00
################################################################################

[2026-01-10 15:00:00] Connecting to Cassandra at ['localhost']:9042...
[2026-01-10 15:00:00] ✓ Connected successfully

================================================================================
TEST 1: Request Count and Latency Metrics
================================================================================
[2026-01-10 15:00:01] Generating 2000 read/write operations...
[2026-01-10 15:00:01] Performing WRITE operations...
  → Written 100 records
  → Written 200 records
...

📊 Expected Metrics:
  • cassandra.client.request.count: Should show ~2000 requests
  • cassandra.client.request.latency: Should show average latency

################################################################################
# ALL TESTS COMPLETED
################################################################################
```

## 🔍 Verification

After running tests, verify metrics in SigNoz:

1. Wait 1-2 minutes for OpenTelemetry to collect metrics
2. Open your SigNoz dashboard
3. Search for these metrics:
   - `cassandra.client.request.count`
   - `cassandra.client.request.latency`
   - `cassandra.storage.load`
   - `cassandra.compaction.tasks.pending`
   - `jvm.memory.heap.used`

### Using nodetool

```bash
# Check cluster status
docker compose exec cassandra nodetool status

# Check node info
docker compose exec cassandra nodetool info

# Check table stats
docker compose exec cassandra nodetool cfstats metrics_test

# Check compaction
docker compose exec cassandra nodetool compactionstats
```

## 🧹 Cleanup

Remove test data:

```bash
docker compose exec cassandra cqlsh -e "DROP KEYSPACE metrics_test;"
```

## 📁 Files Created

The script creates:
- **Keyspace:** `metrics_test`
- **Tables:** `test_data`, `large_data`

## ⚠️ Notes

1. **Cassandra must be running** before executing tests
2. **Port 9042** must be accessible from the test machine
3. **Compaction metrics** may show 0 (normal for small datasets)
4. **Metrics appear in SigNoz** after 1-2 minute delay (collection interval)

## 🔗 Related Files

- `test_compaction_simple.sh` - Shell script for compaction testing
- `test_compaction_aggressive.py` - Aggressive compaction test
- `requirements.txt` - Python dependencies

