int total = 0;
Action<int> add = x => total += x;     // captures and mutates total
add(5); add(7);
Console.WriteLine(total);

var fromFor = new List<Func<int>>();
for (int i = 0; i < 3; i++) fromFor.Add(() => i);
Console.WriteLine(string.Join(",", fromFor.Select(f => f())));

var fixedFor = new List<Func<int>>();
for (int i = 0; i < 3; i++) { int copy = i; fixedFor.Add(() => copy); }
Console.WriteLine(string.Join(",", fixedFor.Select(f => f())));

var fromForeach = new List<Func<int>>();
foreach (var n in new[] { 0, 1, 2 }) fromForeach.Add(() => n);
Console.WriteLine(string.Join(",", fromForeach.Select(f => f())));

var counter = MakeCounter();
counter(); counter();
Console.WriteLine(counter());

Func<int, int> doubler = static x => x * 2;
Console.WriteLine(doubler(21));

TryParse<int> parse = (text, out result) => int.TryParse(text, out result);   // C# 14
Console.WriteLine(parse("12", out var parsed) ? parsed : -1);
var withDefault = (int step = 10) => step * 3;
Console.WriteLine(withDefault());

static Func<int> MakeCounter()
{
    int count = 0;                      // lives on in the closure after MakeCounter returns
    return () => ++count;
}

delegate bool TryParse<T>(string text, out T result);
