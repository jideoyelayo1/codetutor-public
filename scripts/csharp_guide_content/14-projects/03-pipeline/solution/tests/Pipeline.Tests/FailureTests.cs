using Pipeline;

namespace Pipeline.Tests;

public class FailureTests
{
    [Fact]
    public async Task WorkerFailureCancelsSiblingsAndSurfacesTheCause()
    {
        int running = 0, started = 0;
        var run = BoundedPipeline.RunAsync(Enumerable.Range(0, 1000), capacity: 2, workers: 3, async (n, ct) =>
        {
            Interlocked.Increment(ref started);
            Interlocked.Increment(ref running);
            try
            {
                if (n == 1) throw new InvalidDataException("bad item 1");   // reached while siblings are blocked
                await Task.Delay(Timeout.Infinite, ct);   // only cancellation ends these workers
                return 1;
            }
            finally { Interlocked.Decrement(ref running); }
        }, TestContext.Current.CancellationToken);

        var error = await Assert.ThrowsAsync<InvalidDataException>(() => run);
        Assert.Equal("bad item 1", error.Message);
        Assert.Equal(0, Volatile.Read(ref running));      // no worker outlives RunAsync
        Assert.InRange(started, 2, 10);
    }

    [Fact]
    public async Task WorkerOwnCancellationStopsTheWholeRun()
    {
        var run = BoundedPipeline.RunAsync(Enumerable.Range(0, 1000), capacity: 1, workers: 2, async (n, ct) =>
        {
            if (n == 1) throw new OperationCanceledException("worker's own timeout");   // pipeline token still active
            await Task.Delay(Timeout.Infinite, ct);
            return 1;
        }, TestContext.Current.CancellationToken);

        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => run);
    }

    [Fact]
    public async Task SourceFailureCancelsBusyWorkers()
    {
        static IEnumerable<int> Source()
        {
            yield return 0;
            yield return 1;
            throw new InvalidDataException("source broke");
        }
        var run = BoundedPipeline.RunAsync(Source(), capacity: 1, workers: 1, async (n, ct) =>
        {
            await Task.Delay(Timeout.Infinite, ct);   // only cancellation releases the worker
            return 1;
        }, TestContext.Current.CancellationToken);

        var error = await Assert.ThrowsAsync<InvalidDataException>(() => run);
        Assert.Equal("source broke", error.Message);
    }
}
