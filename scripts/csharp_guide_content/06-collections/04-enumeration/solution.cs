var stock = new Dictionary<string, int> { ["a"] = 1, ["b"] = 0, ["c"] = 0, ["d"] = 2 };
foreach (var key in stock.Where(kv => kv.Value == 0).Select(kv => kv.Key).ToList())
    stock.Remove(key);
Console.WriteLine(string.Join(",", stock.Keys.Order()));
