using var cts = new CancellationTokenSource();
int processed = 0;
int total = await ProcessAsync([1, 2, 3, 4, 5], cts.Token, () => { if (++processed == 3) cts.Cancel(); });
Console.WriteLine($"partial total {total} after {processed} items");

static async Task<int> ProcessAsync(int[] items, CancellationToken token, Action progress)
{
    int sum = 0;
    try
    {
        foreach (var item in items)
        {
            token.ThrowIfCancellationRequested();
            sum += item;
            progress();
            await Task.Yield();
        }
    }
    catch (OperationCanceledException) when (token.IsCancellationRequested) { }
    return sum;
}
