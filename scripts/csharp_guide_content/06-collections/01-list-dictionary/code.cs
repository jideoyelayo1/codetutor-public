var names = new List<string>(capacity: 4) { "Cleo", "Ada" };
names.Add("Bob");
names.Insert(0, "Zed");
names.Remove("Cleo");
names.Sort();
Console.WriteLine($"{string.Join(",", names)} count={names.Count}");
Console.WriteLine(names.IndexOf("Bob"));

string text = "the cat and the hat and the bat";
var counts = new Dictionary<string, int>();
foreach (var word in text.Split(' '))
    counts[word] = counts.GetValueOrDefault(word) + 1;
foreach (var key in counts.Keys.Order())
    Console.Write($"{key}={counts[key]} ");
Console.WriteLine();

Console.WriteLine(counts.TryGetValue("dog", out int dogs) ? dogs : -1);
try { counts.Add("the", 1); }
catch (ArgumentException) { Console.WriteLine("duplicate key rejected by Add"); }

var caseless = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase) { ["Ada"] = 1 };
Console.WriteLine(caseless.ContainsKey("ADA"));
