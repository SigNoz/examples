#!/usr/bin/env python3
"""
Cassandra Metrics Testing Suite
This script generates workload to test all monitored Cassandra metrics:
1. cassandra.client.request.count - Total read/write requests
2. cassandra.client.request.latency - Request latency
3. cassandra.compaction.tasks.pending - Pending compaction tasks
4. cassandra.storage.load - Data size on disk
5. jvm.memory.heap.used - JVM heap memory usage
6. jvm.gc.collections.count - Garbage collection count
7. jvm.gc.collections.elapsed - Time spent in GC
"""

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import time
import random
import string
import sys
import argparse
from datetime import datetime

class CassandraMetricsTester:
    def __init__(self, contact_points=['localhost'], port=9042):
        self.contact_points = contact_points
        self.port = port
        self.cluster = None
        self.session = None
        
    def connect(self):
        """Establish connection to Cassandra cluster"""
        print(f"[{self.get_timestamp()}] Connecting to Cassandra at {self.contact_points}:{self.port}...")
        try:
            self.cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port
            )
            self.session = self.cluster.connect()
            print(f"[{self.get_timestamp()}] ✓ Connected successfully")
            return True
        except Exception as e:
            print(f"[{self.get_timestamp()}] ✗ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close connection to Cassandra"""
        if self.cluster:
            self.cluster.shutdown()
            print(f"[{self.get_timestamp()}] Disconnected from Cassandra")
    
    def get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def setup_test_keyspace(self):
        """Create test keyspace and tables"""
        print(f"\n[{self.get_timestamp()}] Setting up test keyspace and tables...")
        
        # Create keyspace
        self.session.execute("""
            CREATE KEYSPACE IF NOT EXISTS metrics_test
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        print(f"[{self.get_timestamp()}] ✓ Keyspace 'metrics_test' created")
        
        # Use the keyspace
        self.session.set_keyspace('metrics_test')
        
        # Create test table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id UUID PRIMARY KEY,
                data TEXT,
                timestamp BIGINT,
                value INT
            )
        """)
        print(f"[{self.get_timestamp()}] ✓ Table 'test_data' created")
        
        # Create table with large data for storage testing
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS large_data (
                id UUID PRIMARY KEY,
                large_text TEXT,
                timestamp BIGINT
            )
        """)
        print(f"[{self.get_timestamp()}] ✓ Table 'large_data' created")
    
    def generate_random_string(self, length):
        """Generate random string of given length"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def test_request_count_and_latency(self, num_operations=1000):
        """
        Test: cassandra.client.request.count and cassandra.client.request.latency
        Generates read/write operations to produce metrics
        """
        print(f"\n{'='*80}")
        print(f"TEST 1: Request Count and Latency Metrics")
        print(f"{'='*80}")
        print(f"[{self.get_timestamp()}] Generating {num_operations} read/write operations...")
        
        # Prepare statement for better performance
        insert_stmt = self.session.prepare("""
            INSERT INTO test_data (id, data, timestamp, value)
            VALUES (uuid(), ?, ?, ?)
        """)
        
        write_count = 0
        read_count = 0
        
        # Perform write operations
        print(f"[{self.get_timestamp()}] Performing WRITE operations...")
        for i in range(num_operations // 2):
            self.session.execute(
                insert_stmt,
                (self.generate_random_string(100), int(time.time()), random.randint(1, 1000))
            )
            write_count += 1
            if (i + 1) % 100 == 0:
                print(f"  → Written {i + 1} records")
        
        print(f"[{self.get_timestamp()}] ✓ Completed {write_count} WRITE operations")
        
        # Perform read operations
        print(f"[{self.get_timestamp()}] Performing READ operations...")
        for i in range(num_operations // 2):
            rows = list(self.session.execute("SELECT * FROM test_data LIMIT 10"))
            read_count += 1
            if (i + 1) % 100 == 0:
                print(f"  → Completed {i + 1} reads")
        
        print(f"[{self.get_timestamp()}] ✓ Completed {read_count} READ operations")
        print(f"\n📊 Expected Metrics:")
        print(f"  • cassandra.client.request.count: Should show ~{num_operations} requests")
        print(f"  • cassandra.client.request.latency: Should show average latency for reads/writes")
    
    def test_storage_load(self, num_records=5000, data_size_kb=10):
        """
        Test: cassandra.storage.load
        Inserts large amounts of data to increase storage metrics
        """
        print(f"\n{'='*80}")
        print(f"TEST 2: Storage Load Metric")
        print(f"{'='*80}")
        print(f"[{self.get_timestamp()}] Inserting {num_records} records with ~{data_size_kb}KB each...")
        
        insert_stmt = self.session.prepare("""
            INSERT INTO large_data (id, large_text, timestamp)
            VALUES (uuid(), ?, ?)
        """)
        
        # Generate large text data (approximately data_size_kb in size)
        large_text = self.generate_random_string(data_size_kb * 1024)
        
        for i in range(num_records):
            self.session.execute(
                insert_stmt,
                (large_text, int(time.time()))
            )
            if (i + 1) % 500 == 0:
                print(f"  → Inserted {i + 1} records (~{(i + 1) * data_size_kb / 1024:.2f} MB)")
        
        total_size_mb = (num_records * data_size_kb) / 1024
        print(f"[{self.get_timestamp()}] ✓ Inserted ~{total_size_mb:.2f} MB of data")
        print(f"\n📊 Expected Metrics:")
        print(f"  • cassandra.storage.load: Should increase by ~{total_size_mb:.2f} MB")
    
    def test_compaction_tasks(self):
        """
        Test: cassandra.compaction.tasks.pending
        Forces compactions by creating multiple SSTables
        """
        print(f"\n{'='*80}")
        print(f"TEST 3: Compaction Tasks Metric")
        print(f"{'='*80}")
        print(f"[{self.get_timestamp()}] Creating multiple SSTables to trigger compaction...")
        
        # Insert data in batches with flush between insertions
        # This creates multiple SSTables which will trigger compaction
        for batch in range(5):
            print(f"[{self.get_timestamp()}] Writing batch {batch + 1}/5...")
            insert_stmt = self.session.prepare("""
                INSERT INTO test_data (id, data, timestamp, value)
                VALUES (uuid(), ?, ?, ?)
            """)
            
            for i in range(500):
                self.session.execute(
                    insert_stmt,
                    (self.generate_random_string(200), int(time.time()), random.randint(1, 1000))
                )
            
            print(f"  → Batch {batch + 1} completed")
            time.sleep(1)  # Small delay between batches
        
        print(f"[{self.get_timestamp()}] ✓ Created multiple SSTables")
        print(f"\n📊 Expected Metrics:")
        print(f"  • cassandra.compaction.tasks.pending: Should show pending compaction tasks")
        print(f"  • Note: Compaction may happen automatically, check nodetool compactionstats")
    
    def test_jvm_memory_and_gc(self, num_operations=10000):
        """
        Test: jvm.memory.heap.used, jvm.gc.collections.count, jvm.gc.collections.elapsed
        Creates memory pressure to trigger garbage collection
        """
        print(f"\n{'='*80}")
        print(f"TEST 4: JVM Memory and GC Metrics")
        print(f"{'='*80}")
        print(f"[{self.get_timestamp()}] Creating memory pressure with {num_operations} operations...")
        
        # Create lots of objects to trigger GC
        insert_stmt = self.session.prepare("""
            INSERT INTO test_data (id, data, timestamp, value)
            VALUES (uuid(), ?, ?, ?)
        """)
        
        for i in range(num_operations):
            # Create larger data to use more memory
            large_data = self.generate_random_string(500)
            self.session.execute(
                insert_stmt,
                (large_data, int(time.time()), random.randint(1, 1000))
            )
            
            if (i + 1) % 1000 == 0:
                print(f"  → Completed {i + 1} operations")
        
        print(f"[{self.get_timestamp()}] ✓ Memory pressure test completed")
        print(f"\n📊 Expected Metrics:")
        print(f"  • jvm.memory.heap.used: Should show increased heap usage")
        print(f"  • jvm.gc.collections.count: Should show increased GC count")
        print(f"  • jvm.gc.collections.elapsed: Should show time spent in GC")
    
    def run_all_tests(self):
        """Run all metric tests"""
        print(f"\n{'#'*80}")
        print(f"# CASSANDRA METRICS TESTING SUITE")
        print(f"# Starting at: {self.get_timestamp()}")
        print(f"{'#'*80}\n")
        
        if not self.connect():
            print("Failed to connect to Cassandra. Exiting.")
            return False
        
        try:
            # Setup
            self.setup_test_keyspace()
            
            # Test 1: Request count and latency
            self.test_request_count_and_latency(num_operations=2000)
            time.sleep(5)  # Brief pause between tests
            
            # Test 2: Storage load
            self.test_storage_load(num_records=3000, data_size_kb=10)
            time.sleep(5)
            
            # Test 3: Compaction tasks
            self.test_compaction_tasks()
            time.sleep(5)
            
            # Test 4: JVM memory and GC
            self.test_jvm_memory_and_gc(num_operations=5000)
            
            print(f"\n{'#'*80}")
            print(f"# ALL TESTS COMPLETED")
            print(f"# Finished at: {self.get_timestamp()}")
            print(f"{'#'*80}\n")
            
            print("\n📋 NEXT STEPS:")
            print("1. Wait 1-2 minutes for metrics to be collected by OpenTelemetry")
            print("2. Check your SigNoz dashboard for the following metrics:")
            print("   • cassandra.client.request.count")
            print("   • cassandra.client.request.latency")
            print("   • cassandra.compaction.tasks.pending")
            print("   • cassandra.storage.load")
            print("   • jvm.memory.heap.used")
            print("   • jvm.gc.collections.count")
            print("   • jvm.gc.collections.elapsed")
            print("\n3. Run 'docker compose exec cassandra nodetool status' to verify node health")
            print("4. Run 'docker compose exec cassandra nodetool info' for detailed metrics")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Test Cassandra metrics')
    parser.add_argument('--host', default='localhost', help='Cassandra host (default: localhost)')
    parser.add_argument('--port', type=int, default=9042, help='Cassandra port (default: 9042)')
    parser.add_argument('--test', choices=['all', 'requests', 'storage', 'compaction', 'jvm'],
                       default='all', help='Which test to run')
    
    args = parser.parse_args()
    
    tester = CassandraMetricsTester(contact_points=[args.host], port=args.port)
    
    if args.test == 'all':
        success = tester.run_all_tests()
    else:
        if not tester.connect():
            print("Failed to connect to Cassandra.")
            sys.exit(1)
        
        try:
            tester.setup_test_keyspace()
            
            if args.test == 'requests':
                tester.test_request_count_and_latency(num_operations=2000)
            elif args.test == 'storage':
                tester.test_storage_load(num_records=3000, data_size_kb=10)
            elif args.test == 'compaction':
                tester.test_compaction_tasks()
            elif args.test == 'jvm':
                tester.test_jvm_memory_and_gc(num_operations=5000)
            
            success = True
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            success = False
        finally:
            tester.disconnect()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
