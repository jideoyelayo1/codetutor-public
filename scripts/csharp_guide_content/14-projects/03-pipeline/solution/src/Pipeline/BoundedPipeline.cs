using System.Threading.Channels;

namespace Pipeline;

/// <summary>Feeds items through a bounded channel to a fixed number of workers and sums their results.</summary>
public static class BoundedPipeline
{
    public static async Task<long> RunAsync<T>(
        IEnumerable<T> items, int capacity, int workers,
        Func<T, CancellationToken, ValueTask<int>> work, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(items);
        ArgumentNullException.ThrowIfNull(work);
        ArgumentOutOfRangeException.ThrowIfLessThan(capacity, 1);
        ArgumentOutOfRangeException.ThrowIfLessThan(workers, 1);

        // Owned by this run: a failing worker cancels its siblings and the producer.
        using var failure = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        var token = failure.Token;
        var channel = Channel.CreateBounded<T>(new BoundedChannelOptions(capacity) { SingleWriter = true });
        long total = 0;

        async Task ProduceAsync()
        {
            try
            {
                foreach (var item in items) await channel.Writer.WriteAsync(item, token);
                channel.Writer.Complete();
            }
            catch (Exception e)
            {
                channel.Writer.TryComplete(e);
                failure.Cancel();   // a failing source must also stop workers already inside work()
                throw;
            }
        }

        async Task ConsumeAsync()
        {
            try
            {
                await foreach (var item in channel.Reader.ReadAllAsync(token))
                    Interlocked.Add(ref total, await work(item, token));
            }
            catch
            {
                // Any exit by exception, including work()'s own cancellation, stops the whole run.
                failure.Cancel();
                throw;
            }
        }

        var tasks = new List<Task> { ProduceAsync() };
        for (int i = 0; i < workers; i++) tasks.Add(ConsumeAsync());
        Task all = Task.WhenAll(tasks);
        try
        {
            await all;
        }
        catch when (all.Exception?.InnerExceptions.FirstOrDefault(e => e is not OperationCanceledException) is { } cause)
        {
            // Every task has finished here, so no work outlives the call; report the real failure, not a sibling's cancellation.
            System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(cause).Throw();
        }
        return total;
    }
}
