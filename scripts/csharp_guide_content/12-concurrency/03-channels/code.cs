using System.Collections.Concurrent;
using System.Threading.Channels;

var counts = new ConcurrentDictionary<string, int>();
Parallel.ForEach(new[] { "a", "b", "a", "c", "a", "b" }, word => counts.AddOrUpdate(word, 1, (_, n) => n + 1));
Console.WriteLine(string.Join(" ", counts.OrderBy(kv => kv.Key).Select(kv => $"{kv.Key}={kv.Value}")));

var channel = Channel.CreateBounded<int>(new BoundedChannelOptions(2) { FullMode = BoundedChannelFullMode.Wait });
var events = new ConcurrentQueue<string>();
var gate = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);

Task producer = Task.Run(async () =>
{
    for (int i = 1; i <= 4; i++)
    {
        var write = channel.Writer.WriteAsync(i);
        if (!write.IsCompleted) { events.Enqueue($"producer waits at item {i}"); gate.TrySetResult(); }
        await write;
    }
    channel.Writer.Complete();
});

await gate.Task;                          // the producer is now blocked by backpressure
int total = 0;
await foreach (var item in channel.Reader.ReadAllAsync())
    total += item;
await producer;
Console.WriteLine(events.First());
Console.WriteLine($"consumed total {total}, reader completed: {channel.Reader.Completion.IsCompleted}");

var work = Channel.CreateUnbounded<int>();
for (int i = 1; i <= 100; i++) work.Writer.TryWrite(i);
work.Writer.Complete();
var perWorker = await Task.WhenAll(Enumerable.Range(0, 3).Select(async _ =>
{
    int sum = 0;
    await foreach (var n in work.Reader.ReadAllAsync()) sum += n;
    return sum;
}));
Console.WriteLine($"3 consumers shared the work: {perWorker.Sum()}");
