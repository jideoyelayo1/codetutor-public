string name = "Ada";
int age = 36;
Console.WriteLine($"{name} is {age} years old");
Console.WriteLine($"price: {19.5:F2}");
Console.WriteLine($"|{"left",-8}|{"right",8}|");
string fruit = "banana";
string plural = fruit + "s";
Console.WriteLine(plural);
Console.WriteLine(fruit[^3..]);
Console.WriteLine(@"C:\temp\new");
string json = $$"""
    {"name": "{{name}}"}
    """;
Console.WriteLine(json);
Console.WriteLine(string.Equals("ADA", name, StringComparison.OrdinalIgnoreCase).ToString().ToLowerInvariant());
