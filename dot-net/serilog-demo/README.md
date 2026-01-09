# Serilog + OpenTelemetry Demo API

A production-ready ASP.NET Core Web API demonstrating **Serilog** structured logging and **OpenTelemetry** distributed tracing with **SigNoz Cloud** integration.

## Features

✨ **Serilog Structured Logging**
- Console output with structured JSON properties
- Request/response logging with trace context
- Log correlation with distributed traces
- **OTLP log export to SigNoz** (via Serilog.Sinks.OpenTelemetry)

🔭 **OpenTelemetry Distributed Tracing**
- Automatic HTTP instrumentation (ASP.NET Core + HttpClient)
- Custom activity/span creation with events
- Trace context propagation (W3C Trace Context)
- Dual exporters: Console (local debugging) + OTLP (SigNoz)

🎯 **Demo Endpoints**
- `GET /health` - Health check
- `GET /api/data` - Fetch data with trace events
- `POST /api/data` - Create data with structured logging
- `GET /api/external` - HTTP call with trace propagation
- `GET /api/error` - Error handling demonstration

## Prerequisites

### 1. SigNoz Cloud Account

1. **Sign up** for SigNoz Cloud at [https://signoz.io/](https://signoz.io/)
2. **Navigate** to Settings → Ingestion Settings
3. **Copy your Ingestion Key** - you'll need this
4. **Note your region** (e.g., `in`, `us`, `eu`)

> **Tip**: Keep your ingestion key handy - you'll set it as an environment variable

### 2. Development Environment

- **.NET SDK 10.0 or later**
  ```bash
  dotnet --version  # Should show 10.0.x or higher
  ```
- **Git** (to clone the repository)
- **curl** or similar tool for testing (optional)

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/SigNoz/signoz-examples.git
cd signoz-examples/dotnet/serilog-demo
```


### Step 2: Configure SigNoz Credentials

You have two options to configure your SigNoz credentials:

#### Option 1: Using launchSettings.json (Recommended for Local Development)

Edit `Properties/launchSettings.json` and add your SigNoz credentials:

```json
{
  "profiles": {
    "http": {
      "environmentVariables": {
        "ASPNETCORE_ENVIRONMENT": "Development",
        "SigNoz__Region": "in",
        "SigNoz__IngestionKey": "your-actual-key-here"
      }
    }
  }
}
```

> **Note**: Replace `your-actual-key-here` with your actual SigNoz ingestion key. The double underscore (`__`) represents nested configuration (`SigNoz:Region` in appsettings.json).

#### Option 2: Using Environment Variables

Export environment variables in your shell before running:

```bash
export SigNoz__Region=in
export SigNoz__IngestionKey=your-actual-key-here
```

### Step 3: Run the Application

```bash
dotnet run
```

You should see:
```
[10:49:53 INF] Starting serilog-demo-api v1.0.0
[10:49:53 INF] OpenTelemetry configured: logs and traces → SigNoz (in)
[10:49:53 INF] Now listening on: http://localhost:5242
```

If SigNoz is not configured, you'll see:
```
[10:49:53 WRN] SigNoz not configured. Set SigNoz__Region and SigNoz__IngestionKey environment variables.
[10:49:53 INF] Logs and traces will only be exported to Console.
```


The API is now running on `http://localhost:5242` (or the port shown in your console).

### Step 4: Generate Sample Traffic

In a **new terminal**, run the load generator:

```bash
chmod +x load-generator.sh
./load-generator.sh
```

This script will continuously make requests to all endpoints, generating logs and traces.

### Step 5: View in SigNoz

1. Go to your [SigNoz Cloud dashboard](https://signoz.io)
2. Navigate to **Services**
3. Click on **serilog-demo-api**
4. Explore:
   - **Traces** - See distributed traces with parent-child relationships
   - **Logs** See structured logs correlated with traces

## What You'll See

### Console Output

The application outputs both **Serilog logs** and **OpenTelemetry traces**:

**Logs:**
```
[10:50:29 INF] Creating new data item: {"Name": "Test Item", "Category": "Demo"}
[10:50:29 INF] Created data item with ID: 1, Name: Test Item, Category: Demo
```

**Traces:**
```
Activity.TraceId:            4efbaf00c6a28ba6fad2635ba453a020
Activity.SpanId:             82e941c42965055c
Activity.DisplayName:        CreateData
Activity.Tags:
    data.name: Test Item
    data.category: Demo
Activity.Events:
    DataItemCreated
```

### SigNoz Dashboard

🔍 **Trace View**: See complete HTTP request traces with nested spans  
📊 **Service Metrics**: Request rates, latencies, error rates  
🎯 **Trace Propagation**: Observe how trace context flows to external services  
❌ **Error Tracking**: Errors from `/api/error` endpoint with full stack traces

## Testing Individual Endpoints

```bash
# Health check
curl http://localhost:5242/health

# Get all data
curl http://localhost:5242/api/data

# Create new data
curl -X POST http://localhost:5242/api/data \
  -H "Content-Type: application/json" \
  -d '{"name":"My Item","category":"Electronics"}'

# External service call (with trace propagation)
curl http://localhost:5242/api/external

# Trigger error (for error tracking demo)
curl http://localhost:5242/api/error
```

## Configuration

This project uses a **hybrid configuration approach** following 12-Factor App principles:

| Configuration Type | Where It Lives | Example |
|-------------------|----------------|---------|
| **Static settings** | `appsettings.json` | Log levels, enrichers, console format |
| **Secrets/Dynamic** | Environment variables | API keys, endpoints |

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------:|
| `SigNoz__Region` | Your SigNoz cloud region | `in`, `us`, `eu` |
| `SigNoz__IngestionKey` | Your SigNoz ingestion key | `abc123...` |
| `ServiceInfo__Name` | Service name (optional) | `my-api` |
| `ServiceInfo__Version` | Service version (optional) | `2.0.0` |

> **Note**: The double underscore (`__`) is .NET's convention for nested configuration paths.

### appsettings.json

Contains static Serilog configuration:
- Log levels and overrides
- Enrichers (FromLogContext, WithSpan, WithMachineName)
- Console sink with output template

OpenTelemetry sinks (logs + traces) are configured in code to use environment variables for secrets.

## Project Structure

```
serilog-demo/
├── Controllers/
│   ├── DataController.cs      # GET/POST with trace events
│   ├── ExternalController.cs  # Trace propagation demo
│   └── ErrorController.cs     # Error handling demo
├── Models/
│   └── DataItem.cs            # Data model
├── Properties/
│   └── launchSettings.json    # Local dev environment variables
├── Program.cs                 # App configuration (Serilog + OTEL)
├── appsettings.json           # Static Serilog config
├── load-generator.sh          # Traffic generator script
└── README.md                  # This file
```

## Key Features Demonstrated

### 1. Structured Logging (Serilog)
```csharp
_logger.LogInformation("Created data item with ID: {Id}, Name: {Name}", 
    newItem.Id, newItem.Name);
```

### 2. Custom Trace Events
```csharp
activity?.AddEvent(new ActivityEvent("DataItemCreated",
    tags: new ActivityTagsCollection
    {
        { "item.id", newItem.Id },
        { "item.name", newItem.Name }
    }));
```

### 3. Trace Propagation
The `ExternalController` automatically propagates W3C Trace Context headers to `httpbin.org`:
- `traceparent`: Contains trace ID, span ID, and flags

### 4. Log-Trace Correlation
Logs include `TraceId` and `SpanId` for correlation:
```json
{
  "TraceId": "4efbaf00c6...",
  "SpanId": "82e941..."
}
```

## Troubleshooting

**Problem**: "Missing SigNoz configuration" warning
- **Solution**: Set both `SIGNOZ_REGION` and `SIGNOZ_INGESTION_KEY` environment variables

**Problem**: Traces not appearing in SigNoz
- **Check**: Are both environment variables set correctly?
- **Check**: Is the region correct?
- **Check**: Wait 30-60 seconds for data to appear

**Problem**: Port already in use
- **Solution**: The app uses a dynamic port. Check the console output for the actual port

## Learn More

- [SigNoz Documentation](https://signoz.io/docs/)
- [OpenTelemetry .NET](https://opentelemetry.io/docs/languages/net/)
- [Serilog Documentation](https://serilog.net/)

## License

This example is part of the SigNoz examples repository. See the main repository for license information.
