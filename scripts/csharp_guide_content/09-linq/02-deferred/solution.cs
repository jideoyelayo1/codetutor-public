var names = new List<string> { "Ada", "Grace", "Alan" };
var longNames = names.Where(n => n.Length > 3).Select(n => n.ToUpperInvariant());
Console.WriteLine(string.Join(",", longNames));
names.Add("Barbara");
Console.WriteLine(string.Join(",", longNames));
var frozen = longNames.ToArray();
names.Add("Edsger");
Console.WriteLine($"{frozen.Length} {longNames.Count()}");
