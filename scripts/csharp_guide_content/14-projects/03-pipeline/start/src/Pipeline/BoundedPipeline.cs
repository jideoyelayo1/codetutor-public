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

        var channel = Channel.CreateBounded<T>(new BoundedChannelOptions(capacity) { SingleWriter = true });
        long total = 0;

        async Task ProduceAsync()
        {
            try
            {
                foreach (var item in items) await channel.Writer.WriteAsync(item, cancellationToken);
                channel.Writer.Complete();
            }
            catch (Exception e)
            {
                channel.Writer.TryComplete(e);
                throw;
            }
        }

        async Task ConsumeAsync()
        {
            await foreach (var item in channel.Reader.ReadAllAsync(cancellationToken))
                Interlocked.Add(ref total, await work(item, cancellationToken));
        }

        var tasks = new List<Task> { ProduceAsync() };
        for (int i = 0; i < workers; i++) tasks.Add(ConsumeAsync());
        await Task.WhenAll(tasks);
        return total;
    }
}
