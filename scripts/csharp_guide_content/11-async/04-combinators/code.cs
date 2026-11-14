var ok = Task.FromResult(1);
var bad1 = Task.FromException<int>(new InvalidOperationException("first"));
var bad2 = Task.FromException<int>(new ArgumentException("second"));
Task<int[]> all = Task.WhenAll(ok, bad1, bad2);
try { await all; }
catch (InvalidOperationException e) { Console.WriteLine($"await rethrows: {e.Message}"); }
Console.WriteLine($"all failures: {string.Join(", ", all.Exception!.InnerExceptions.Select(x => x.Message))}");

var slow = new TaskCompletionSource<string>();
var fast = new TaskCompletionSource<string>();
Task<Task<string>> race = Task.WhenAny(slow.Task, fast.Task);
fast.SetResult("fast wins");
Task<string> winner = await race;
Console.WriteLine(await winner);
slow.SetResult("slow finished later");

var sources = Enumerable.Range(0, 3).Select(_ => new TaskCompletionSource<int>()).ToArray();
var order = new List<int>();
Task consume = Consume();
sources[2].SetResult(2); sources[0].SetResult(0); sources[1].SetResult(1);
await consume;
Console.WriteLine($"completion order: {string.Join(",", order)}");

var never = new TaskCompletionSource<int>();
try { await never.Task.WaitAsync(TimeSpan.FromMilliseconds(30)); }
catch (TimeoutException) { Console.WriteLine($"gave up waiting; task still {never.Task.Status}"); }

int peak = 0, running = 0;
await Parallel.ForEachAsync(Enumerable.Range(0, 20), new ParallelOptions { MaxDegreeOfParallelism = 3 }, async (i, ct) =>
{
    int now = Interlocked.Increment(ref running);
    InterlockedMax(ref peak, now);
    await Task.Delay(5, ct);
    Interlocked.Decrement(ref running);
});
Console.WriteLine($"never more than 3 at once: {peak <= 3}");

async Task Consume()
{
    await foreach (var t in Task.WhenEach(sources.Select(s => s.Task)))
        order.Add(await t);
}

static void InterlockedMax(ref int target, int value)
{
    int current;
    while ((current = Volatile.Read(ref target)) < value && Interlocked.CompareExchange(ref target, value, current) != current) { }
}
