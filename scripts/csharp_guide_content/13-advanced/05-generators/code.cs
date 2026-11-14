using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

Console.WriteLine(Patterns.Date.IsMatch("2026-10-16"));
Console.WriteLine(Patterns.Date.IsMatch("16/10/2026"));
var match = Patterns.Date.Match("released 2025-11-11");
Console.WriteLine(match.Groups["year"].Value);
Console.WriteLine(Patterns.Words().Count("one two  three"));

var lesson = new Lesson("Source generators", 13);
string json = JsonSerializer.Serialize(lesson, GuideJson.Default.Lesson);
Console.WriteLine(json);
Lesson back = JsonSerializer.Deserialize(json, GuideJson.Default.Lesson)!;
Console.WriteLine(back == lesson);

static partial class Patterns
{
    [GeneratedRegex(@"(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})")]
    public static partial Regex Date { get; }          // C# 13 partial property

    [GeneratedRegex(@"\w+")]
    public static partial Regex Words();
}

record Lesson(string Title, int Stage);

[JsonSourceGenerationOptions(PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase)]
[JsonSerializable(typeof(Lesson))]
partial class GuideJson : JsonSerializerContext;
