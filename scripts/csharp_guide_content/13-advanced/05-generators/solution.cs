using System.Text.RegularExpressions;

foreach (var input in new[] { "#A1B2C3", "#12345", "abc123" })
    Console.WriteLine($"{input} {Colors.Hex().IsMatch(input)}");

static partial class Colors
{
    [GeneratedRegex("^#[0-9a-f]{6}$", RegexOptions.IgnoreCase)]
    public static partial Regex Hex();
}
