int? maybe = null;
Console.WriteLine(maybe.HasValue);
Console.WriteLine(maybe.GetValueOrDefault(-1));
Console.WriteLine((maybe + 1) is null);
maybe = 41;
Console.WriteLine(maybe.Value + 1);

string? name = FindName(2);
Console.WriteLine(name?.Length ?? 0);
if (name is null)
{
    Console.WriteLine("not found");
}
name = FindName(1);
if (name is { } found)               // non-null pattern: found is a string
    Console.WriteLine(found.ToUpperInvariant());
Console.WriteLine(Describe(null));

static string? FindName(int id) => id == 1 ? "ada" : null;
static string Describe(string? text) => text switch
{
    null => "(null)",
    "" => "(empty)",
    _ => text,
};
