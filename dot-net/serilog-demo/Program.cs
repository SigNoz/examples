using Serilog;
using Serilog.Enrichers.Span;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Exporter;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);

// ===== Configure Serilog =====
// All configuration is in appsettings.json
// Override with environment variables:
//   - SigNoz__Region (e.g., "in", "us", "eu")
//   - SigNoz__IngestionKey (your SigNoz ingestion key)
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .CreateLogger();

builder.Host.UseSerilog();

Log.Information("Starting serilog-demo-api v1.0.0");

// Read configuration values
var serviceName = builder.Configuration.GetValue<string>("Serilog:WriteTo:1:Args:resourceAttributes:service.name") ?? "serilog-demo-api";
var serviceVersion = builder.Configuration.GetValue<string>("Serilog:WriteTo:1:Args:resourceAttributes:service.version") ?? "1.0.0";
var signozRegion = builder.Configuration.GetValue<string>("SigNoz:Region");
var signozIngestionKey = builder.Configuration.GetValue<string>("SigNoz:IngestionKey");

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
        var signozEndpoint = $"https://ingest.{signozRegion}.signoz.cloud:443";
        tracerProviderBuilder.AddOtlpExporter(options =>
        {
            options.Endpoint = new Uri(signozEndpoint);
            options.Protocol = OtlpExportProtocol.Grpc;
            options.Headers = $"signoz-ingestion-key={signozIngestionKey}";
        });
        Log.Information("OTLP trace exporter configured for SigNoz region: {Region}", signozRegion);
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
