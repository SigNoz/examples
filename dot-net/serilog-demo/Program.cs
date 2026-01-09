using Serilog;
using Serilog.Enrichers.Span;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Exporter;
using System.Diagnostics;
using DotNetEnv;

// Load .env file if it exists
Env.Load();

var builder = WebApplication.CreateBuilder(args);

// ===== Configure Service Info and SigNoz =====
var serviceName = "serilog-demo-api";
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

// ===== Configure Serilog =====
// Load base configuration from appsettings.json
var serilogConfig = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration);

// Add OpenTelemetry sink if SigNoz is configured
if (!string.IsNullOrEmpty(signozRegion) && !string.IsNullOrEmpty(signozIngestionKey))
{
    var signozEndpoint = $"https://ingest.{signozRegion}.signoz.cloud:443/v1/logs";
    serilogConfig.WriteTo.OpenTelemetry(options =>
    {
        options.Endpoint = signozEndpoint;
        options.Protocol = Serilog.Sinks.OpenTelemetry.OtlpProtocol.Grpc;
        options.Headers = new Dictionary<string, string>
        {
            ["signoz-ingestion-key"] = signozIngestionKey
        };
        options.ResourceAttributes = new Dictionary<string, object>
        {
            ["service.name"] = serviceName,
            ["service.version"] = serviceVersion
        };
    });
    Log.Information("OTLP log exporter configured for SigNoz region: {Region}", signozRegion);
}

Log.Logger = serilogConfig.CreateLogger();

builder.Host.UseSerilog();

if (missingVars.Count > 0)
{
    Log.Warning("Missing SigNoz configuration: {MissingVariables}. Traces and logs will only be exported to console.",
        string.Join(", ", missingVars));
}

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

Log.Information("Starting {ServiceName} v{ServiceVersion}", serviceName, serviceVersion);

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
