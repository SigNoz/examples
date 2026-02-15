#!/usr/bin/env node

const http = require('http');

// Configuration
const config = {
  baseUrl: 'http://localhost:3000/api',
  interval: 3000, // 3 seconds between requests
  verbose: true,
};

// Test scenarios
const scenarios = [
  {
    name: 'Get Users (Basic Tracing)',
    method: 'GET',
    path: '/users',
    weight: 3, // Higher weight = more frequent
  },
  {
    name: 'Create User (Custom Tracing)',
    method: 'POST',
    path: '/users',
    headers: { 'Content-Type': 'application/json' },
    body: () =>
      JSON.stringify({
        name: `User ${Math.floor(Math.random() * 1000)}`,
        email: `user${Math.floor(Math.random() * 1000)}@test.com`,
      }),
    weight: 2,
  },
  {
    name: 'Get User by ID (With Error Simulation)',
    method: 'GET',
    path: () => `/users/${Math.random() > 0.7 ? 'nonexistent' : '1'}`, // 30% error rate
    weight: 2,
  },
  {
    name: 'Search Users',
    method: 'GET',
    path: '/users/search?email=john',
    weight: 1,
  },
  {
    name: 'Create Order (Distributed Tracing)',
    method: 'POST',
    path: '/orders',
    headers: { 'Content-Type': 'application/json' },
    body: () =>
      JSON.stringify({
        userId: Math.floor(Math.random() * 3) + 1,
        items: [
          {
            productId: `prod-${Math.floor(Math.random() * 100)}`,
            quantity: Math.floor(Math.random() * 5) + 1,
            price: Math.round((Math.random() * 100 + 10) * 100) / 100,
          },
        ],
        totalAmount: Math.round((Math.random() * 200 + 50) * 100) / 100,
        paymentMethod: ['credit_card', 'debit_card', 'paypal'][
          Math.floor(Math.random() * 3)
        ],
      }),
    weight: 2,
  },
  {
    name: 'Get Orders',
    method: 'GET',
    path: '/orders',
    weight: 1,
  },
  {
    name: 'Health Check (Ignored by Tracing)',
    method: 'GET',
    path: '/health',
    weight: 1,
  },
  {
    name: 'App Info',
    method: 'GET',
    path: '/info',
    weight: 1,
  },
];

// Create weighted scenario list
function createWeightedScenarios() {
  const weighted = [];
  scenarios.forEach((scenario) => {
    for (let i = 0; i < scenario.weight; i++) {
      weighted.push(scenario);
    }
  });
  return weighted;
}

const weightedScenarios = createWeightedScenarios();

// Make HTTP request
function makeRequest(scenario) {
  return new Promise((resolve, reject) => {
    const path =
      typeof scenario.path === 'function' ? scenario.path() : scenario.path;
    const body = scenario.body ? scenario.body() : null;

    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api${path}`,
      method: scenario.method,
      headers: scenario.headers || {},
    };

    if (body) {
      options.headers['Content-Length'] = Buffer.byteLength(body);
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          data: data,
          headers: res.headers,
        });
      });
    });

    req.on('error', reject);

    if (body) {
      req.write(body);
    }

    req.end();
  });
}

// Execute test scenario
async function executeScenario() {
  const scenario =
    weightedScenarios[Math.floor(Math.random() * weightedScenarios.length)];
  const startTime = Date.now();

  try {
    const response = await makeRequest(scenario);
    const duration = Date.now() - startTime;

    if (config.verbose) {
      const status = response.statusCode < 400 ? '✅' : '❌';
      const timestamp = new Date().toLocaleTimeString();
      console.log(
        `${status} [${timestamp}] ${scenario.method} ${scenario.name} ` +
          `→ ${response.statusCode} (${duration}ms)`,
      );

      // Show response for errors or interesting responses
      if (response.statusCode >= 400 || scenario.name.includes('Create')) {
        try {
          const parsed = JSON.parse(response.data);
          console.log(`   Response: ${JSON.stringify(parsed, null, 0)}`);
        } catch (e) {
          console.log(`   Response: ${response.data.substring(0, 100)}...`);
        }
      }
    }

    return { success: true, duration, statusCode: response.statusCode };
  } catch (error) {
    const duration = Date.now() - startTime;
    if (config.verbose) {
      console.log(
        `❌ [${new Date().toLocaleTimeString()}] ${scenario.name} → ERROR (${duration}ms): ${error.message}`,
      );
    }
    return { success: false, duration, error: error.message };
  }
}

// Statistics tracking
const stats = {
  requests: 0,
  successful: 0,
  errors: 0,
  totalDuration: 0,
  startTime: Date.now(),
};

// Main execution loop
async function runTests() {
  console.log('🚀 OpenTelemetry Trace Generator Started');
  console.log(`📊 Hitting ${config.baseUrl} every ${config.interval}ms`);
  console.log('📋 Test scenarios:');
  scenarios.forEach((s) => console.log(`   - ${s.name} (weight: ${s.weight})`));
  console.log('');
  console.log('🔄 Generating traces... (Press Ctrl+C to stop)');
  console.log('');

  const interval = setInterval(async () => {
    const result = await executeScenario();

    // Update statistics
    stats.requests++;
    stats.totalDuration += result.duration;

    if (result.success) {
      stats.successful++;
    } else {
      stats.errors++;
    }

    // Show periodic statistics
    if (stats.requests % 20 === 0) {
      const uptime = Math.round((Date.now() - stats.startTime) / 1000);
      const avgDuration = Math.round(stats.totalDuration / stats.requests);
      const successRate = Math.round((stats.successful / stats.requests) * 100);

      console.log('');
      console.log('📊 Statistics:');
      console.log(
        `   Requests: ${stats.requests} | Success: ${stats.successful} | Errors: ${stats.errors}`,
      );
      console.log(
        `   Success Rate: ${successRate}% | Avg Duration: ${avgDuration}ms | Uptime: ${uptime}s`,
      );
      console.log('');
    }
  }, config.interval);

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n');
    console.log('🛑 Stopping trace generator...');
    clearInterval(interval);

    const uptime = Math.round((Date.now() - stats.startTime) / 1000);
    const avgDuration =
      stats.requests > 0 ? Math.round(stats.totalDuration / stats.requests) : 0;
    const successRate =
      stats.requests > 0
        ? Math.round((stats.successful / stats.requests) * 100)
        : 0;

    console.log('');
    console.log('📊 Final Statistics:');
    console.log(`   Total Requests: ${stats.requests}`);
    console.log(`   Successful: ${stats.successful}`);
    console.log(`   Errors: ${stats.errors}`);
    console.log(`   Success Rate: ${successRate}%`);
    console.log(`   Average Duration: ${avgDuration}ms`);
    console.log(`   Total Runtime: ${uptime}s`);
    console.log('');
    console.log('✅ Trace generation completed!');

    process.exit(0);
  });
}

// Command line options
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
🔧 OpenTelemetry Trace Generator

Usage:
  node test-traces.js [options]

Options:
  --fast         Use 1 second intervals (instead of 3s)
  --slow         Use 5 second intervals
  --quiet        Reduce output verbosity
  --help, -h     Show this help

Examples:
  node test-traces.js --fast      # Generate traces every second
  node test-traces.js --quiet     # Less verbose output
  npm run test:traces             # Using npm script

This script generates realistic traces by hitting various endpoints:
- GET requests (automatic HTTP tracing)
- POST requests (custom business logic tracing)  
- Error scenarios (exception tracing)
- Distributed operations (multi-span tracing)

Perfect for testing your OpenTelemetry setup and generating data for screenshots!
`);
  process.exit(0);
}

if (args.includes('--fast')) {
  config.interval = 1000;
}

if (args.includes('--slow')) {
  config.interval = 5000;
}

if (args.includes('--quiet')) {
  config.verbose = false;
}

// Start the test generator
runTests().catch(console.error);
