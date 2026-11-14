using System.Runtime.CompilerServices;

await foreach (var page in PagesAsync(3)) Console.WriteLine(page);

using var cts = new CancellationTokenSource();
await foreach (var page in PagesAsync(100).WithCancellation(cts.Token))
{
    Console.WriteLine($"got {page}");
    if (page == "page 2") break;          // disposes the enumerator, running finally
}

await using (var connection = new Connection())
{
    await connection.SendAsync("hello");
}

var cache = new SquareCache();
Console.WriteLine(await cache.GetAsync(4));
Console.WriteLine(await cache.GetAsync(4));
Console.WriteLine($"computed {cache.Computations} time(s)");

static async IAsyncEnumerable<string> PagesAsync(int count, [EnumeratorCancellation] CancellationToken token = default)
{
    try
    {
        for (int i = 1; i <= count; i++)
        {
            await Task.Yield();
            token.ThrowIfCancellationRequested();
            yield return $"page {i}";
        }
    }
    finally { Console.WriteLine($"pages finished"); }
}

sealed class Connection : IAsyncDisposable
{
    public async Task SendAsync(string message) { await Task.Yield(); Console.WriteLine($"sent {message}"); }
    public async ValueTask DisposeAsync() { await Task.Yield(); Console.WriteLine("flushed and closed"); }
}

sealed class SquareCache
{
    private readonly Dictionary<int, int> values = [];
    public int Computations { get; private set; }
    public ValueTask<int> GetAsync(int n) =>
        values.TryGetValue(n, out int hit) ? ValueTask.FromResult(hit) : new ValueTask<int>(ComputeAsync(n));
    private async Task<int> ComputeAsync(int n)
    {
        await Task.Yield();
        Computations++;
        return values[n] = n * n;
    }
}
