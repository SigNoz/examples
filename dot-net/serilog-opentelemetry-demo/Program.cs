using Serilog;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Exporter;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);

// =============================================================================
// CONFIGURATION APPROACH (Hybrid - 12-Factor App Pattern)
// =============================================================================
// Static config (log levels, enrichers, console sink) → appsettings.json
// Dynamic config (API keys, endpoints)                → Environment variables
//
// Environment variables (use double underscore for nested paths):
//   - SigNoz__Region        → SigNoz region (in, us, eu)
//   - SigNoz__IngestionKey  → Your SigNoz ingestion key
//   - ServiceInfo__Name     → Service name (optional override)
//   - ServiceInfo__Version  → Service version (optional override)
// =============================================================================

// Read service info from configuration (can be overridden via env vars)
var serviceName = builder.Configuration.GetValue<string>("ServiceInfo:Name") ?? "serilog-demo-api";
var serviceVersion = builder.Configuration.GetValue<string>("ServiceInfo:Version") ?? "1.0.0";

// Read SigNoz configuration from environment variables
var signozRegion = builder.Configuration.GetValue<string>("SigNoz:Region");
var signozIngestionKey = builder.Configuration.GetValue<string>("SigNoz:IngestionKey");

var isValidSigNozRegion = !string.IsNullOrEmpty(signozRegion) && signozRegion != "<your-region>";
var isValidSigNozIngestionKey = !string.IsNullOrEmpty(signozIngestionKey) && signozIngestionKey != "<your-signoz-ingestion-key>";
var hasSigNozConfig = isValidSigNozRegion && isValidSigNozIngestionKey;

// =============================================================================
// SERILOG CONFIGURATION
// =============================================================================
// Base config (levels, enrichers, console sink) is loaded from appsettings.json
// OpenTelemetry sink is added here because it needs dynamic values (secrets)
// =============================================================================

var loggerConfig = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration);

// Add OpenTelemetry log sink if SigNoz is configured
if (hasSigNozConfig)
{
    var signozLogsEndpoint = $"https://ingest.{signozRegion}.signoz.cloud:443/v1/logs";
    loggerConfig.WriteTo.OpenTelemetry(options =>
    {
        options.Endpoint = signozLogsEndpoint;
        options.Protocol = Serilog.Sinks.OpenTelemetry.OtlpProtocol.Grpc;
        options.Headers = new Dictionary<string, string>
        {
            ["signoz-ingestion-key"] = signozIngestionKey!
        };
        options.ResourceAttributes = new Dictionary<string, object>
        {
            ["service.name"] = serviceName,
            ["service.version"] = serviceVersion
        };
    });
}

Log.Logger = loggerConfig.CreateLogger();
builder.Host.UseSerilog();

Log.Information("Starting {ServiceName} v{ServiceVersion}", serviceName, serviceVersion);

// =============================================================================
// OPENTELEMETRY TRACING CONFIGURATION
// =============================================================================
// Trace exporter also configured here to use the same SigNoz credentials
// =============================================================================

builder.Services.AddOpenTelemetry()
    .WithTracing(tracerProviderBuilder =>
    {
        tracerProviderBuilder
            .AddSource(serviceName)
            .SetResourceBuilder(
                ResourceBuilder.CreateDefault()
                    .AddService(serviceName: serviceName, serviceVersion: serviceVersion))
            .AddAspNetCoreInstrumentation(options =>
            {
                options.RecordException = true;
                options.EnrichWithHttpRequest = (activity, request) =>
                {
                    activity.SetTag("http.client_ip", request.HttpContext.Connection.RemoteIpAddress?.ToString());
                };
            })
            .AddHttpClientInstrumentation(options =>
            {
                options.RecordException = true;
            })
            .AddConsoleExporter();

        // Add OTLP exporter for SigNoz if configured
        if (hasSigNozConfig)
        {
            var signozTracesEndpoint = $"https://ingest.{signozRegion}.signoz.cloud:443";
            tracerProviderBuilder.AddOtlpExporter(options =>
            {
                options.Endpoint = new Uri(signozTracesEndpoint);
                options.Protocol = OtlpExportProtocol.Grpc;
                options.Headers = $"signoz-ingestion-key={signozIngestionKey}";
            });
            Log.Information("OpenTelemetry configured: logs and traces → SigNoz ({Region})", signozRegion);
        }
        else
        {
            Log.Warning("SigNoz not configured. Set SigNoz__Region and SigNoz__IngestionKey environment variables.");
            Log.Information("Logs and traces will only be exported to Console.");
        }
    });

// Add services
builder.Services.AddControllers();
builder.Services.AddHttpClient(); // Required for ExternalController
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Add Serilog request logging
app.UseSerilogRequestLogging(options =>
{
    options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
    {
        diagnosticContext.Set("ClientIP", httpContext.Connection.RemoteIpAddress);
        diagnosticContext.Set("UserAgent", httpContext.Request.Headers["User-Agent"].ToString());

        // Add trace context to logs
        var activity = Activity.Current;
        if (activity != null)
        {
            diagnosticContext.Set("TraceId", activity.TraceId.ToString());
            diagnosticContext.Set("SpanId", activity.SpanId.ToString());
        }
    };
});

app.MapControllers();

// Add a simple health check endpoint
app.MapGet("/health", () => new
{
    Status = "Healthy",
    Service = serviceName,
    Version = serviceVersion,
    Timestamp = DateTime.UtcNow
}).WithName("HealthCheck");

Log.Information("Application started successfully");

try
{
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}
