string[] words = ["apple", "avocado", "banana", "blueberry", "cherry"];
var groups = new Dictionary<char, List<string>>();
foreach (var w in words)
{
    if (!groups.TryGetValue(w[0], out var list))
    {
        list = [];
        groups[w[0]] = list;
    }
    list.Add(w);
}
foreach (var key in groups.Keys.Order())
    Console.WriteLine($"{key}: {string.Join(",", groups[key])}");
