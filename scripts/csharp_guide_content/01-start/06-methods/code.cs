Console.WriteLine(Square(5));

int counter = 1;
BumpCopy(counter);
Console.WriteLine($"after Bump(copy): {counter}");
Bump(ref counter);
Console.WriteLine($"after Bump(ref): {counter}");

foreach (var text in new[] { "42", "abc" })
{
    if (int.TryParse(text, out int value)) Console.WriteLine($"parsed {value}");
    else Console.WriteLine($"not a number: {text}");
}

Console.WriteLine(Sum(1, 2, 3, 4));
Console.WriteLine(Greet("Ada"));
Console.WriteLine(Greet(punctuation: "?", name: "Bob", greeting: "Hi"));
Printer.Describe(1);
Printer.Describe(1.0);

static int Square(int x) => x * x;
static void BumpCopy(int x) => x++;
static void Bump(ref int x) => x++;
static int Sum(params int[] values)
{
    int total = 0;
    foreach (int v in values) total += v;
    return total;
}
static string Greet(string name, string greeting = "Hello", string punctuation = "!") => $"{greeting}, {name}{punctuation}";
static class Printer
{
    public static void Describe(int _) => Console.WriteLine("int overload");
    public static void Describe(double _) => Console.WriteLine("double overload");
}
