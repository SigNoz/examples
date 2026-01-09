using Microsoft.AspNetCore.Mvc;
using SerilogOtelApi.Models;
using System.Diagnostics;

namespace SerilogOtelApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class DataController : ControllerBase
{
    private static readonly List<DataItem> _dataStore = new();
    private static int _nextId = 1;
    private readonly ILogger<DataController> _logger;
    private static readonly ActivitySource ActivitySource = new("serilog-otel-demo-api");

    public DataController(ILogger<DataController> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// GET /api/data - Returns all stored data items
    /// </summary>
    [HttpGet]
    public ActionResult<IEnumerable<DataItem>> GetData()
    {
        using var activity = ActivitySource.StartActivity("GetData");
        activity?.SetTag("data.count", _dataStore.Count);

        _logger.LogInformation("Fetching all data items. Current count: {Count}", _dataStore.Count);

        // Add trace event to the current activity
        activity?.AddEvent(new ActivityEvent("DataRetrievalStarted"));

        var result = _dataStore.ToList();

        activity?.AddEvent(new ActivityEvent("DataRetrievalCompleted", 
            tags: new ActivityTagsCollection { { "result.count", result.Count } }));

        _logger.LogInformation("Retrieved {Count} data items successfully", result.Count);

        return Ok(result);
    }

    /// <summary>
    /// POST /api/data - Creates a new data item
    /// </summary>
    [HttpPost]
    public ActionResult<DataItem> CreateData([FromBody] CreateDataRequest request)
    {
        using var activity = ActivitySource.StartActivity("CreateData");
        activity?.SetTag("data.name", request.Name);
        activity?.SetTag("data.category", request.Category);

        _logger.LogInformation("Creating new data item: {@Request}", request);

        var newItem = new DataItem
        {
            Id = _nextId++,
            Name = request.Name,
            Category = request.Category,
            CreatedAt = DateTime.UtcNow
        };

        _dataStore.Add(newItem);

        // Add trace event with structured data
        activity?.AddEvent(new ActivityEvent("DataItemCreated",
            tags: new ActivityTagsCollection
            {
                { "item.id", newItem.Id },
                { "item.name", newItem.Name },
                { "item.category", newItem.Category }
            }));

        _logger.LogInformation("Created data item with ID: {Id}, Name: {Name}, Category: {Category}", 
            newItem.Id, newItem.Name, newItem.Category);

        return CreatedAtAction(nameof(GetData), new { id = newItem.Id }, newItem);
    }
}

public record CreateDataRequest(string Name, string Category);
