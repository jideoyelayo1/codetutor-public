Console.WriteLine(Initials("ada", "lovelace"));
Console.WriteLine(Initials(null, "turing"));
Console.WriteLine(Initials(null, null));

static string Initials(string? first, string? last)
{
    string result = "";
    foreach (var part in new[] { first, last })
    {
        if (!string.IsNullOrEmpty(part)) result += char.ToUpperInvariant(part[0]) + ".";
    }
    return result.Length == 0 ? "?" : result;
}
