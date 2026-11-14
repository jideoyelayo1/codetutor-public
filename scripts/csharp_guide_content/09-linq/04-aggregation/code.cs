string[] words = ["apple", "bob", "cherry", "ant", "bee", "cat", "apple"];
Console.WriteLine(words.Count(w => w.StartsWith('a')));
Console.WriteLine(words.MaxBy(w => w.Length));
Console.WriteLine(words.Max(w => w.Length));
Console.WriteLine(words.Aggregate("", (acc, w) => acc + w[0]));
Console.WriteLine(string.Join(",", words.DistinctBy(w => w[0])));

foreach (var (letter, count) in words.CountBy(w => w[0]).OrderBy(p => p.Key))
    Console.Write($"{letter}{count} ");
Console.WriteLine();
foreach (var (letter, total) in words.AggregateBy(w => w[0], 0, (sum, w) => sum + w.Length).OrderBy(p => p.Key))
    Console.Write($"{letter}{total} ");
Console.WriteLine();

foreach (var (index, word) in words.Index().Where(p => p.Item.Length > 4))
    Console.Write($"{index}:{word} ");
Console.WriteLine();

foreach (var batch in Enumerable.Range(1, 7).Chunk(3)) Console.Write($"[{string.Join(",", batch)}]");
Console.WriteLine();
Console.WriteLine(string.Join(",", Enumerable.Range(1, 10).Take(^3..)));
Console.WriteLine(new[] { 1, 2 }.Zip(["one", "two"], (n, s) => $"{n}={s}").Last());

int[] none = [];
Console.WriteLine(none.FirstOrDefault(-1));
try { Console.WriteLine(none.Average()); }
catch (InvalidOperationException) { Console.WriteLine("Average of empty sequence throws"); }
Console.WriteLine(none.Select(x => (int?)x).Max() is null);
