namespace SerilogOtelApi.Models;

public class DataItem
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public string Category { get; set; } = string.Empty;
}
