long total = 0;
var tasks = Enumerable.Range(0, 8).Select(_ => Task.Run(() =>
{
    for (int i = 1; i <= 1000; i++) Interlocked.Add(ref total, i);
}));
await Task.WhenAll(tasks);
Console.WriteLine(total);
