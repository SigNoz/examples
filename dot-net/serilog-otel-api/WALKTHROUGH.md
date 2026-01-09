# Technical Walkthrough: Serilog + OpenTelemetry Integration

This document explains the technical implementation details of the Serilog and OpenTelemetry integration in this demo application.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ASP.NET Core Web API                     │
│                                                               │
│  ┌─────────────────┐         ┌──────────────────┐           │
│  │   Controllers   │         │   Middleware     │           │
│  │  - Data         │◄────────┤  - Request Log   │           │
│  │  - External     │         │  - Exception     │           │
│  │  - Error        │         └──────────────────┘           │
│  └────────┬────────┘                                         │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────┐         ┌──────────────────┐           │
│  │    Serilog      │         │  OpenTelemetry   │           │
│  │  - Structured   │         │  - ActivitySource│           │
│  │    Logging      │         │  - Instrumentation│          │
│  │  - Enrichers    │         │  - Propagation   │           │
│  └────────┬────────┘         └────────┬─────────┘           │
│           │                            │                      │
└───────────┼────────────────────────────┼──────────────────────┘
            │                            │
            ▼                            ▼
    ┌───────────────┐          ┌─────────────────┐
    │   Console     │          │  OTLP Exporter  │
    │   Output      │          │  (SigNoz Cloud) │
    └───────────────┘          └─────────────────┘
```

## Serilog Configuration

### Basic Setup (Program.cs)

```csharp
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithEnvironmentName()
    .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} {Properties:j}{NewLine}{Exception}")
    .CreateLogger();

builder.Host.UseSerilog();
```

**Key Points:**
- **Minimum Level**: INFO for app code, WARNING for ASP.NET internals
- **Enrichers**: Machine name, environment name automatically added
- **Output Template**: Structured format with JSON properties

### Request Logging with Trace Context

```csharp
app.UseSerilogRequestLogging(options =>
{
    options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
    {
        diagnosticContext.Set("ClientIP", httpContext.Connection.RemoteIpAddress);
        diagnosticContext.Set("UserAgent", httpContext.Request.Headers["User-Agent"]);
        
        // Add trace context to logs
        var activity = Activity.Current;
        if (activity != null)
        {
            diagnosticContext.Set("TraceId", activity.TraceId.ToString());
            diagnosticContext.Set("SpanId", activity.SpanId.ToString());
        }
    };
});
```

**Result**: Every HTTP request log includes `TraceId` and `SpanId` for correlation with traces.

## OpenTelemetry Configuration

### Tracing Setup

```csharp
builder.Services.AddOpenTelemetry()
    .WithTracing(tracerProviderBuilder =>
    {
        tracerProviderBuilder
            .AddSource(serviceName)  // Our custom ActivitySource
            .SetResourceBuilder(
                ResourceBuilder.CreateDefault()
                    .AddService(serviceName, serviceVersion))
            .AddAspNetCoreInstrumentation(options =>
            {
                options.RecordException = true;
                options.EnrichWithHttpRequest = (activity, request) =>
                {
                    activity.SetTag("http.client_ip", request.HttpContext.Connection.RemoteIpAddress);
                };
            })
            .AddHttpClientInstrumentation(options =>
            {
                options.RecordException = true;
            })
            .AddConsoleExporter()
            .AddOtlpExporter(/* SigNoz config */);
    });
```

**Components:**
1. **ActivitySource**: Custom spans/activities
2. **ASP.NET Core Instrumentation**: Auto-traces HTTP requests
3. **HttpClient Instrumentation**: Auto-traces outgoing HTTP calls
4. **Exporters**: Console (debug) + OTLP (SigNoz)

### Custom Activities with Events

**DataController Example:**
```csharp
private static readonly ActivitySource ActivitySource = new("serilog-otel-demo-api");

[HttpGet]
public ActionResult<IEnumerable<DataItem>> GetData()
{
    using var activity = ActivitySource.StartActivity("GetData");
    activity?.SetTag("data.count", _dataStore.Count);
    
    // Add trace event
    activity?.AddEvent(new ActivityEvent("DataRetrievalStarted"));
    
    var result = _dataStore.ToList();
    
    activity?.AddEvent(new ActivityEvent("DataRetrievalCompleted",
        tags: new ActivityTagsCollection { { "result.count", result.Count } }));
    
    _logger.LogInformation("Retrieved {Count} data items", result.Count);
    
    return Ok(result);
}
```

**Output Structure:**
```
Activity.TraceId:            3ad9d234ad47a966942113ebcc00e896
Activity.SpanId:             6f57aaf042122705
Activity.ParentSpanId:       8757f627f66cfd8a  ← Links to HTTP request span
Activity.DisplayName:        GetData
Activity.Tags:
    data.count: 0
Activity.Events:
    DataRetrievalStarted
    DataRetrievalCompleted
        result.count: 0
```

## Trace Context Propagation

### How It Works

1. **Incoming Request**:
   - ASP.NET Core instrumentation reads `traceparent` header
   - Creates Activity with matched TraceId

2. **Controller Processing**:
   - Custom Activity created as child span
   - `Activity.Current` provides trace context

3. **Outgoing HTTP Call**:
   - HttpClient instrumentation injects `traceparent` header
   - External service receives trace context

### ExternalController Implementation

```csharp
[HttpGet]
public async Task<ActionResult> CallExternalService()
{
    using var activity = ActivitySource.StartActivity("CallExternalService");
    
    var traceId = Activity.Current?.TraceId.ToString();
    _logger.LogInformation("TraceId: {TraceId}", traceId);
    
    var client = _httpClientFactory.CreateClient();
    var response = await client.GetAsync("https://httpbin.org/headers");
    
    // httpbin.org echoes back the traceparent header it received
    var content = await response.Content.ReadAsStringAsync();
    
    return Ok(new { TraceId = traceId, Response = content });
}
```

**W3C Trace Context Header Format:**
```
traceparent: 00-4efbaf00c6a28ba6fad2635ba453a020-82e941c42965055c-01
             ││  └────────── TraceId ─────────┘  └── SpanId ──┘  └─ Flags
             │└─ Version
             └─ Header identifier
```

## Error Handling & Tracing

### ErrorController Pattern

```csharp
[HttpGet]
public ActionResult TriggerError()
{
    using var activity = ActivitySource.StartActivity("TriggerError");
    
    try
    {
        throw new InvalidOperationException("Demo error");
    }
    catch (Exception ex)
    {
        // Mark activity as error
        activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
        
        // Add exception details to trace
        activity?.AddEvent(new ActivityEvent("ExceptionThrown",
            tags: new ActivityTagsCollection
            {
                { "exception.type", ex.GetType().Name },
                { "exception.message", ex.Message },
                { "exception.stacktrace", ex.StackTrace ?? "" }
            }));
        
        _logger.LogError(ex, "Error occurred. TraceId: {TraceId}", 
            Activity.Current?.TraceId);
        
        return StatusCode(500, new { Error = ex.Message });
    }
}
```

**Benefits:**
- Exception appears in trace with full details
- Activity status set to Error (visible in SigNoz)
- Logs correlated via TraceId

## SigNoz Integration

### OTLP Exporter Configuration

```csharp
if (!string.IsNullOrEmpty(signozRegion) && !string.IsNullOrEmpty(signozIngestionKey))
{
    var signozEndpoint = $"https://ingest.{signozRegion}.signoz.cloud:443";
    tracerProviderBuilder.AddOtlpExporter(options =>
    {
        options.Endpoint = new Uri(signozEndpoint);
        options.Protocol = OtlpExportProtocol.Grpc;
        options.Headers = $"signoz-ingestion-key={signozIngestionKey}";
    });
}
```

**Protocol**: gRPC (efficient binary protocol)  
**Authentication**: Via `signoz-ingestion-key` header  
**Data Format**: OTLP (OpenTelemetry Protocol)

### What Gets Sent to SigNoz

For each trace:
- **Service metadata**: name, version, instance ID
- **Span hierarchy**: parent-child relationships
- **Tags/Attributes**: Custom key-value pairs
- **Events**: Timestamped log points within spans
- **Status**: OK, Error, or Unset
- **Duration**: Automatic span timing

## Log-Trace Correlation

### How Correlation Works

1. **OpenTelemetry** creates Activity (span) for HTTP request
2. **Serilog** request logging middleware captures `Activity.Current`
3. **TraceId and SpanId** added to log properties
4. **Both systems** use the same trace context

### Example Correlated Output

**Log Entry:**
```json
{
  "Timestamp": "2026-01-09T05:20:29Z",
  "Level": "Information",
  "Message": "Created data item with ID: 1",
  "TraceId": "4efbaf00c6a28ba6fad2635ba453a020",
  "SpanId": "3e514c30aadb86df",
  "Properties": {
    "Id": 1,
    "Name": "Test Item"
  }
}
```

**Corresponding Trace:**
```
TraceId: 4efbaf00c6a28ba6fad2635ba453a020
├─ Span: POST api/Data (3e514c30aadb86df)
   └─ Span: CreateData (82e941c42965055c)
```

You can search logs by TraceId in your logging system, or view correlated logs directly in SigNoz.

## Performance Considerations

### Minimal Overhead

- **Instrumentation**: < 1ms typical overhead per request
- **Sampling**: Can configure to sample % of traces (disabled in demo)
- **Async Export**: Telemetry export doesn't block requests

### Best Practices

1. **Use ActivitySource** for custom spans (not direct Activity creation)
2. **Limit event data size** - avoid logging huge payloads
3. **Structured logging** - use log properties, not string interpolation
4. **Error sampling** - can log all errors, sample successful requests

## Debugging Tips

### View Traces Locally

Both console exporters output to stdout:
```bash
dotnet run | grep -A 20 "Activity.TraceId"
```

### Check Trace Propagation

```bash
curl -v http://localhost:5000/api/external 2>&1 | grep traceparent
```

### Verify SigNoz Connection

Check logs for:
```
[INF] OTLP exporter configured for SigNoz region: in
```

If missing, environment variables weren't set correctly.

## Further Reading

- **OpenTelemetry .NET**: https://opentelemetry.io/docs/languages/net/
- **Activity API**: https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.activity
- **Serilog**: https://serilog.net/
- **W3C Trace Context**: https://www.w3.org/TR/trace-context/
