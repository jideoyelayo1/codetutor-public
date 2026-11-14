var settings = new Dictionary<string, string> { ["mode"] = "fast" };
foreach (var key in new[] { "mode", "level" })
{
    try { Console.WriteLine(ReadSetting(settings, key)); }
    catch (KeyNotFoundException e) { Console.WriteLine(e.Message); }
}

static string ReadSetting(Dictionary<string, string> settings, string key) =>
    settings.TryGetValue(key, out var value) ? value : throw new KeyNotFoundException($"Setting '{key}' is missing.");
