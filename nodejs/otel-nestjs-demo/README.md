# NestJS OpenTelemetry Demo

A complete, production-ready implementation of OpenTelemetry in NestJS applications. This demo showcases automatic instrumentation, custom tracing, distributed tracing, and integration with observability platforms like SigNoz.

## 🚀 Features

- ✅ **Automatic HTTP instrumentation** - Zero-code request tracing
- ✅ **Custom business logic tracing** - `@Traced` decorator for important operations
- ✅ **Distributed tracing simulation** - Multi-span operations across services
- ✅ **Error handling and exception capture** - Comprehensive error tracing
- ✅ **Production-ready configuration** - Sampling, batching, and performance optimization
- ✅ **Multiple tracer configurations** - Console (dev) and OTLP (production)
- ✅ **Automated trace generation** - Test script for generating demo traces

## 📋 Prerequisites

- Node.js 18.19.0+ or 20.6.0+
- TypeScript 5.0.4+
- NestJS 8.0+ (NestJS 11+ requires Node.js 20+)

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Setup Environment (for SigNoz Cloud)

```bash
# Create .env file from template
npm run setup:env

# Edit .env with your SigNoz credentials:
# SIGNOZ_ENDPOINT=https://ingest.YOUR-REGION.signoz.cloud:443/v1/traces
# SIGNOZ_ACCESS_TOKEN=your-actual-token-here
```

### 3. Choose Your Tracer Configuration

```bash
# For development (console output)
npm run switch:console

# For production (SigNoz Cloud)
npm run switch:signoz
```

### 4. Start the Application

```bash
npm run start:dev
```

### 5. Generate Test Traces

```bash
# In another terminal
npm run test:traces:fast
```

## 📊 Available Endpoints

| Endpoint | Method | Tracing Type | Description |
|----------|--------|--------------|-------------|
| `/api/users` | GET | Custom (`@Traced`) | List users with business logic tracing |
| `/api/users` | POST | Custom (`user_creation`) | Create user with validation tracing |
| `/api/users/:id` | GET | Custom + Error | Get user (includes 404 simulation) |
| `/api/orders` | POST | Distributed | Multi-span order workflow |
| `/api/health` | GET | None (Ignored) | Health check endpoint |

## 🎯 Demo Scenarios

### Basic Tracing
```bash
curl http://localhost:3000/api/users
```

### Custom Business Logic
```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'
```

### Distributed Tracing
```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "1",
    "items": [{"productId": "prod-123", "quantity": 2, "price": 29.99}],
    "totalAmount": 59.98,
    "paymentMethod": "credit_card"
  }'
```

### Error Simulation
```bash
curl http://localhost:3000/api/users/nonexistent
```

## 🧪 Scripts

| Command | Description |
|---------|-------------|
| `npm run start:dev` | Start development server |
| `npm run setup:env` | Create environment file |
| `npm run switch:console` | Use console tracer (development) |
| `npm run switch:signoz` | Use SigNoz tracer (production) |
| `npm run tracer:status` | Check current tracer config |
| `npm run test:traces` | Generate test traces (3s intervals) |
| `npm run test:traces:fast` | Generate test traces (1s intervals) |

## 🏗️ Architecture

```
src/
├── decorators/
│   └── traced.decorator.ts     # @Traced decorator for custom spans
├── user/                       # User module with custom tracing
│   ├── user.service.ts        # Business logic with @Traced
│   ├── user.controller.ts     # HTTP endpoints
│   └── user.module.ts
├── order/                      # Order module with distributed tracing
│   ├── order.service.ts       # Complex multi-span operations
│   ├── order.controller.ts
│   └── order.module.ts
└── health/                     # Health checks (ignored by tracing)
    └── health.controller.ts

tracer.ts                       # Console tracer (development)
tracer.signoz.ts               # SigNoz Cloud tracer
tracer.production.ts           # Production-optimized tracer
test-traces.js                 # Automated trace generator
```

## 🔧 Key Implementation Details

### Critical Initialization Order
```typescript
// tracer MUST be imported and started before NestJS
import tracer from './tracer';
await tracer.start();
import { NestFactory } from '@nestjs/core';
```

### Custom Tracing with Decorators
```typescript
@Injectable()
export class UserService {
  @Traced('user_creation')
  async createUser(userData: CreateUserDto): Promise<User> {
    // Automatically traced with custom span name
  }
}
```

### Distributed Tracing Pattern
```typescript
// Parent span containing multiple child operations
async createOrder() {
  return await this.tracer.startActiveSpan('create_order', async (span) => {
    await this.processPayment();  // Child span
    await this.saveOrder();       // Child span
  });
}
```

## 📈 Observability Platforms

This demo works with any OpenTelemetry-compatible platform:

- **[SigNoz Cloud](https://signoz.io/teams/)** (recommended)
- Jaeger
- Zipkin
- Datadog
- New Relic
- Any OTLP-compatible backend

## 🐛 Troubleshooting

**No traces appearing?**
- Check tracer initialization order
- Verify environment variables
- Use `npm run switch:console` to debug locally

**Performance issues?**
- Use sampling in production (`tracer.production.ts`)
- Disable unnecessary instrumentations
- Configure batch processing

## 📚 Learn More

This implementation demonstrates production-ready OpenTelemetry patterns:
- Automatic vs. manual instrumentation
- Performance optimization techniques
- Error handling and exception capture
- Context propagation across async operations
- Resource management and cleanup

Perfect for learning OpenTelemetry or as a starting point for your own applications!

## 📄 License

MIT
