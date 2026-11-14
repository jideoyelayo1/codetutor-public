string? longest = null;
while (Console.ReadLine() is string line)
{
    string trimmed = line.Trim();
    if (trimmed.Length > 0 && (longest is null || trimmed.Length > longest.Length)) longest = trimmed;
}
Console.WriteLine(longest ?? "(none)");
