using Pipeline;

namespace Pipeline.Tests;

public class BoundedPipelineTests
{
    [Fact]
    public async Task SumsEveryResult()
    {
        long total = await BoundedPipeline.RunAsync(Enumerable.Range(1, 100), capacity: 4, workers: 3,
            (n, _) => ValueTask.FromResult(n), TestContext.Current.CancellationToken);
        Assert.Equal(5050, total);
    }

    [Fact]
    public async Task NeverRunsMoreThanWorkerCountAtOnce()
    {
        int running = 0, peak = 0;
        await BoundedPipeline.RunAsync(Enumerable.Range(0, 40), capacity: 2, workers: 3, async (_, ct) =>
        {
            int now = Interlocked.Increment(ref running);
            int seen;
            while ((seen = Volatile.Read(ref peak)) < now && Interlocked.CompareExchange(ref peak, now, seen) != seen) { }
            await Task.Delay(2, ct);
            Interlocked.Decrement(ref running);
            return 1;
        }, TestContext.Current.CancellationToken);
        Assert.InRange(peak, 1, 3);
    }

    [Fact]
    public async Task ProducerWaitsWhenChannelIsFull()
    {
        int produced = 0;
        var release = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        IEnumerable<int> Source() { for (int i = 0; i < 20; i++) { produced++; yield return i; } }
        var run = BoundedPipeline.RunAsync(Source(), capacity: 2, workers: 1, async (_, _) => { await release.Task; return 1; },
            TestContext.Current.CancellationToken);
        await Task.Delay(100, TestContext.Current.CancellationToken);
        Assert.InRange(produced, 1, 5);        // capacity 2 + one item in the worker + one waiting write
        release.SetResult();
        Assert.Equal(20, await run);
    }

    [Fact]
    public async Task CancellationStopsWorkAndSurfaces()
    {
        using var cts = new CancellationTokenSource();
        int started = 0;
        var run = BoundedPipeline.RunAsync(Enumerable.Range(0, 1000), capacity: 2, workers: 2, async (_, ct) =>
        {
            if (Interlocked.Increment(ref started) == 5) cts.Cancel();
            await Task.Delay(1, ct);
            return 1;
        }, cts.Token);
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => run);
        Assert.InRange(started, 5, 20);
    }

    [Fact]
    public async Task RejectsBadArgumentsBeforeStarting() =>
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() =>
            BoundedPipeline.RunAsync([1], capacity: 0, workers: 1, (n, _) => ValueTask.FromResult(n), TestContext.Current.CancellationToken));
}
