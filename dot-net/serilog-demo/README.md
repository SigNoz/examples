# Serilog + OpenTelemetry Demo

A hands-on example demonstrating how to use Serilog for structured logging and OpenTelemetry for distributed tracing in .NET.

## Setup Complete ✅

- **.NET SDK**: 10.0.101
- **Serilog**: 4.3.0
- **Serilog.Sinks.Console**: 6.1.1
- **OpenTelemetry**: 1.14.0
- **OpenTelemetry.Exporter.Console**: 1.14.0
- **OpenTelemetry.Exporter.OpenTelemetryProtocol**: 1.14.0 (OTLP for SigNoz)

## What's an Activity?

In .NET, an **Activity** is the built-in representation of a **distributed trace span**:
- **Activity = Span** in OpenTelemetry terminology
- Represents a unit of work (method call, HTTP request, etc.)
- Can be nested to show parent-child relationships
- Contains:
  - **TraceId**: Unique ID for the entire trace
  - **SpanId**: Unique ID for this specific span
  - **ParentSpanId**: Links to parent span
  - **Tags/Attributes**: Metadata as key-value pairs
  - **Duration**: Timing information

## SigNoz Integration 🚀

The application is configured to send traces to **SigNoz** using the OTLP exporter.

### Secure Configuration Management

SigNoz configuration (region and ingestion key) is read from **environment variables** to keep them secure and out of your code:

**Option 1: Set for current session**
```bash
export SIGNOZ_REGION='in'  # or 'us', 'eu', etc.
export SIGNOZ_INGESTION_KEY='your-key-here'
dotnet run
```

**Option 2: Inline (one-time use)**
```bash
SIGNOZ_REGION='in' SIGNOZ_INGESTION_KEY='your-key-here' dotnet run
```

**Option 3: Permanent setup (add to ~/.zshrc or ~/.bashrc)**
```bash
echo "export SIGNOZ_REGION='in'" >> ~/.zshrc
echo "export SIGNOZ_INGESTION_KEY='your-key-here'" >> ~/.zshrc
source ~/.zshrc
```

**Helper Script:**
```bash
./setup-signoz.sh  # Check if configuration is set and get instructions
```

### Without SigNoz Configuration

If you run without setting the region or key, the app will:
- ⚠️ Show a warning message listing missing variables
- ✅ Still work normally
- ✅ Export traces to console only (for local debugging)

## Running the Demo

```bash
# Build the project
dotnet build

# Run the application
dotnet run
```

## Output Example

The application produces both **Serilog logs** and **OpenTelemetry traces**:

```
[19:02:21 INF] Application starting up...
[19:02:21 INF] Starting main operation
[19:02:21 DBG] DoWork method called
[19:02:21 INF] Processing user 123 with name John Doe
[19:02:21 WRN] This is a warning message - just for demonstration

Activity.TraceId:            fa000743402cee68aa2a10c12ef03166
Activity.SpanId:             075ceaf5343577cf
Activity.DisplayName:        DoWork
Activity.Tags:
    work.id: d939ef26-f361-49fc-9815-d34e208812fc
    work.status: completed
...
```

## Next Steps

You can now incrementally add features such as:

1. **Serilog Enhancements**
   - File sinks
   - JSON formatting
   - Enrichers (machine name, thread ID, etc.)
   - Minimum level overrides
   - Filtering

2. **OpenTelemetry Enhancements**
   - OTLP exporter (for SigNoz, Jaeger, etc.)
   - HTTP instrumentation
   - Database instrumentation
   - Custom metrics
   - Baggage propagation

3. **Integration**
   - Bridge Serilog logs to OpenTelemetry
   - Correlation between logs and traces
   - Context propagation

## Project Structure

```
serilog-demo/
├── Program.cs              # Main application code
├── SerilogOtelDemo.csproj  # Project file with dependencies
└── README.md               # This file
```

## Ready to Experiment!

The basic setup is complete. You can now:
- Modify `Program.cs` to add more logging statements
- Create additional spans and nested operations
- Experiment with different log levels and structured properties
- Add custom tags to your traces

Let me know when you're ready to add more features! 🚀
