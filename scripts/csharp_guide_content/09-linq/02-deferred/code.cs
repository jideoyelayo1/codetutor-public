var numbers = new List<int> { 1, 2, 3 };
int calls = 0;
var evensSquared = numbers.Where(n => { calls++; return n % 2 == 0; }).Select(n => n * n);
Console.WriteLine($"after defining: calls={calls}");
numbers.Add(4);
Console.WriteLine(string.Join(",", evensSquared));
Console.WriteLine($"after first enumeration: calls={calls}");
Console.WriteLine(evensSquared.Count());
Console.WriteLine($"after Count: calls={calls}");

var snapshot = evensSquared.ToList();
numbers.Add(6);
Console.WriteLine($"snapshot {snapshot.Count}, live {evensSquared.Count()}");

int threshold = 2;
var above = numbers.Where(n => n > threshold);
threshold = 4;
Console.WriteLine(string.Join(",", above));

var trace = new List<string>();
var firstBig = numbers.Select(n => { trace.Add($"s{n}"); return n * 10; }).First(n => n > 15);
Console.WriteLine($"{firstBig} after {string.Join(" ", trace)}");
