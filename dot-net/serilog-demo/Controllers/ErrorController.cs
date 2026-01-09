using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;

namespace SerilogOtelApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ErrorController : ControllerBase
{
    private readonly ILogger<ErrorController> _logger;
    private static readonly ActivitySource ActivitySource = new("serilog-otel-demo-api");

    public ErrorController(ILogger<ErrorController> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// GET /api/error - Intentionally throws an exception to demonstrate error handling and tracing
    /// </summary>
    [HttpGet]
    public ActionResult TriggerError()
    {
        using var activity = ActivitySource.StartActivity("TriggerError");

        var traceId = Activity.Current?.TraceId.ToString();

        _logger.LogInformation("Error endpoint called. TraceId: {TraceId}", traceId);
        activity?.AddEvent(new ActivityEvent("ErrorEndpointInvoked"));

        try
        {
            _logger.LogWarning("About to throw an intentional exception for demonstration");

            // Simulate some work before error
            var random = new Random();
            var processingTime = random.Next(10, 50);
            Thread.Sleep(processingTime);

            activity?.SetTag("processing.time_ms", processingTime);

            // Intentionally throw an exception
            throw new InvalidOperationException("This is a demo error to show how exceptions are traced and logged");
        }
        catch (Exception ex)
        {
            // Set activity status to error
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.AddEvent(new ActivityEvent("ExceptionThrown",
                tags: new ActivityTagsCollection
                {
                    { "exception.type", ex.GetType().Name },
                    { "exception.message", ex.Message },
                    { "exception.stacktrace", ex.StackTrace ?? "" }
                }));

            _logger.LogError(ex, "Error occurred as expected. TraceId: {TraceId}, Message: {Message}",
                traceId, ex.Message);

            return StatusCode(500, new
            {
                Error = "An error occurred",
                Message = ex.Message,
                TraceId = traceId,
                Note = "This error is intentional for demonstration purposes. Check SigNoz to see how errors appear in traces."
            });
        }
    }
}
