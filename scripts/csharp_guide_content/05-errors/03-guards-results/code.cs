using System.Diagnostics.CodeAnalysis;

Console.WriteLine(Rename("report.txt", "summary"));
try { Rename("report.txt", "  "); }
catch (ArgumentException e) { Console.WriteLine(e.Message); }
try { Repeat("ab", -1); }
catch (ArgumentOutOfRangeException e) { Console.WriteLine(e.ParamName); }

foreach (var input in new[] { "#ff8800", "red", "#12" })
{
    if (TryParseColor(input, out var color)) Console.WriteLine($"{input} -> {color}");
    else Console.WriteLine($"{input} -> invalid");
}

foreach (var input in new[] { "ada@example.com", "", "no-at-sign" })
    Console.WriteLine(ValidateEmail(input) switch
    {
        { IsValid: true } r => $"ok {r.Value}",
        var r => $"error {r.Error}",
    });

static string Rename(string path, string newName)
{
    ArgumentException.ThrowIfNullOrWhiteSpace(newName);
    return newName + Path.GetExtension(path);
}

static string Repeat(string text, int count)
{
    ArgumentOutOfRangeException.ThrowIfNegative(count);
    return string.Concat(Enumerable.Repeat(text, count));
}

static bool TryParseColor(string text, [NotNullWhen(true)] out string? rgb)
{
    rgb = null;
    if (text is not ['#', .. var hex] || hex.Length != 6) return false;
    if (!int.TryParse(hex, System.Globalization.NumberStyles.HexNumber, null, out int value)) return false;
    rgb = $"rgb({value >> 16}, {(value >> 8) & 0xFF}, {value & 0xFF})";
    return true;
}

static Result<string> ValidateEmail(string text) => text switch
{
    "" => Result<string>.Fail("empty"),
    _ when !text.Contains('@') => Result<string>.Fail("missing @"),
    _ => Result<string>.Ok(text.ToLowerInvariant()),
};

record Result<T>(bool IsValid, T? Value, string? Error)
{
    public static Result<T> Ok(T value) => new(true, value, null);
    public static Result<T> Fail(string error) => new(false, default, error);
}
