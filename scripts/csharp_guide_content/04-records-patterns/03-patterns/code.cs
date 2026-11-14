object[] inputs = [42, -3, "hi", null!, new Point(0, 5), new Point(2, 2), 3.5];
foreach (var input in inputs) Console.WriteLine(Classify(input));

Console.WriteLine(Grade(95) + Grade(72) + Grade(10));
var order = new Order("open", 250m, new Address("Paris"));
Console.WriteLine(Priority(order));
Console.WriteLine(Priority(order with { Total = 20m }));

static string Classify(object? value) => value switch
{
    null => "null",
    int n when n < 0 => $"negative int {n}",
    int n => $"int {n}",
    string { Length: 0 } => "empty string",
    string s => $"string of {s.Length}",
    Point(0, var y) => $"on the y axis at {y}",
    Point { X: var x, Y: var y } when x == y => "on the diagonal",
    _ => $"something else: {value.GetType().Name}",
};

static string Grade(int score) => score switch
{
    >= 90 => "A",
    >= 70 and < 90 => "C",
    _ => "F",
};

static string Priority(Order o) => o switch
{
    { Status: "open", Total: > 100m, Ship.City: "Paris" } => "rush",
    { Status: "open" } => "normal",
    _ => "none",
};

record Point(int X, int Y);
record Address(string City);
record Order(string Status, decimal Total, Address Ship);
