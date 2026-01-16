using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Text.Json;

namespace SerilogOtelApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ExternalController : ControllerBase
{
    private readonly ILogger<ExternalController> _logger;
    private readonly IHttpClientFactory _httpClientFactory;
    private static readonly ActivitySource ActivitySource = new("serilog-demo-api");

    public ExternalController(ILogger<ExternalController> logger, IHttpClientFactory httpClientFactory)
    {
        _logger = logger;
        _httpClientFactory = httpClientFactory;
    }

    /// <summary>
    /// GET /api/external - Makes HTTP call to external service with trace propagation
    /// Demonstrates W3C Trace Context propagation across service boundaries
    /// </summary>
    [HttpGet]
    public async Task<ActionResult> CallExternalService()
    {
        using var activity = ActivitySource.StartActivity("CallExternalService");

        var traceId = Activity.Current?.TraceId.ToString();
        var spanId = Activity.Current?.SpanId.ToString();

        _logger.LogInformation("Starting external API call. TraceId: {TraceId}, SpanId: {SpanId}",
            traceId, spanId);

        activity?.SetTag("external.service", "httpbin.org");
        activity?.AddEvent(new ActivityEvent("ExternalCallInitiated"));

        try
        {
            var client = _httpClientFactory.CreateClient();

            // The HttpClient instrumentation will automatically propagate trace context
            // via traceparent and tracestate headers (W3C Trace Context)
            _logger.LogInformation("Calling external service: https://httpbin.org/headers");

            var response = await client.GetAsync("https://httpbin.org/headers");
            var content = await response.Content.ReadAsStringAsync();

            activity?.SetTag("http.status_code", (int)response.StatusCode);
            activity?.AddEvent(new ActivityEvent("ExternalCallCompleted",
                tags: new ActivityTagsCollection
                {
                    { "response.status", (int)response.StatusCode },
                    { "response.size", content.Length }
                }));

            // Parse the response to extract and verify trace propagation headers
            string? traceparentHeader = null;
            bool propagationVerified = false;

            try
            {
                var jsonResponse = JsonDocument.Parse(content);
                var headers = jsonResponse.RootElement.GetProperty("headers");

                if (headers.TryGetProperty("Traceparent", out var traceparentElement))
                {
                    traceparentHeader = traceparentElement.GetString();
                    _logger.LogInformation("External API Call Response Traceparent header: {Traceparent}", traceparentHeader);

                    // Verify that the TraceId in the traceparent header matches our current trace
                    // traceparent format: 00-<trace-id>-<span-id>-<flags>
                    if (traceparentHeader != null && traceparentHeader.Contains(traceId?.Replace("-", "") ?? ""))
                    {
                        propagationVerified = true;
                        _logger.LogInformation("Trace context propagation verified! TraceId matches in traceparent header");
                    }
                }
            }
            catch (JsonException jsonEx)
            {
                _logger.LogWarning(jsonEx, "Failed to parse httpbin response for trace verification");
            }

            _logger.LogInformation("External API call completed. Status: {StatusCode}, TraceId: {TraceId}, Propagation: {Verified}",
                response.StatusCode, traceId, propagationVerified ? "VERIFIED" : "NOT DETECTED");

            return Ok(new
            {
                Message = "External service called successfully",
                TraceId = traceId,
                SpanId = spanId,
                StatusCode = response.StatusCode,
                TracePropagation = new
                {
                    Verified = propagationVerified,
                    TraceparentHeader = traceparentHeader ?? "NOT FOUND",
                    FullResponse = content
                }
            });
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.AddEvent(new ActivityEvent("ExternalCallFailed"));

            _logger.LogError(ex, "External API call failed. TraceId: {TraceId}", traceId);

            return StatusCode(500, new
            {
                Error = "External service call failed",
                Message = ex.Message,
                TraceId = traceId
            });
        }
    }
}

