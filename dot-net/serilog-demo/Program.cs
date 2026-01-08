using Serilog;
using OpenTelemetry;
using OpenTelemetry.Trace;
using OpenTelemetry.Resources;
using OpenTelemetry.Exporter;
using System.Diagnostics;

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .WriteTo.Console()
    .CreateLogger();

// Configure OpenTelemetry
var serviceName = "serilog-otel-demo";
var serviceVersion = "1.0.0";

// Read SigNoz configuration from environment variables
var signozRegion = Environment.GetEnvironmentVariable("SIGNOZ_REGION");
var signozIngestionKey = Environment.GetEnvironmentVariable("SIGNOZ_INGESTION_KEY");

// Validate configuration
var missingVars = new List<string>();
if (string.IsNullOrEmpty(signozRegion))
    missingVars.Add("SIGNOZ_REGION");
if (string.IsNullOrEmpty(signozIngestionKey))
    missingVars.Add("SIGNOZ_INGESTION_KEY");

if (missingVars.Any())
{
    Log.Warning("Missing SigNoz configuration: {MissingVariables}. Traces will only be exported to console.",
        string.Join(", ", missingVars));
}

var tracerProviderBuilder = Sdk.CreateTracerProviderBuilder()
    .AddSource(serviceName)
    .SetResourceBuilder(
        ResourceBuilder.CreateDefault()
            .AddService(serviceName: serviceName, serviceVersion: serviceVersion))
    .AddConsoleExporter(); // Keep console exporter for local debugging

// Add OTLP exporter for SigNoz if both region and key are available
if (!string.IsNullOrEmpty(signozRegion) && !string.IsNullOrEmpty(signozIngestionKey))
{
    var signozEndpoint = $"https://ingest.{signozRegion}.signoz.cloud:443";
    tracerProviderBuilder.AddOtlpExporter(options =>
    {
        options.Endpoint = new Uri(signozEndpoint);
        options.Protocol = OtlpExportProtocol.Grpc;
        options.Headers = $"signoz-ingestion-key={signozIngestionKey}";
    });
    Log.Information("OTLP exporter configured for SigNoz region: {Region}", signozRegion);
}

using var tracerProvider = tracerProviderBuilder.Build();

var activitySource = new ActivitySource(serviceName);

// Main program
Log.Information("Application starting up...");

try
{
    // Create a trace span
    using (var activity = activitySource.StartActivity("MainOperation"))
    {
        activity?.SetTag("operation.type", "serilog-demo");

        Log.Information("Starting main operation");

        // Simulate some work
        DoWork();

        Log.Information("Main operation completed successfully");
    }
}
catch (Exception ex)
{
    Log.Error(ex, "An error occurred during execution");
}
finally
{
    Log.Information("Application shutting down...");
    Log.CloseAndFlush();
}

void DoWork()
{
    using (var activity = activitySource.StartActivity("DoWork"))
    {
        activity?.SetTag("work.id", Guid.NewGuid().ToString());

        Log.Debug("DoWork method called");

        // Log with structured data
        var user = new { Name = "John Doe", Id = 123 };
        Log.Information("Processing user {UserId} with name {UserName}", user.Id, user.Name);

        // Simulate some processing
        Thread.Sleep(100);

        Log.Warning("This is a warning message - just for demonstration");

        activity?.SetTag("work.status", "completed");
    }
}
