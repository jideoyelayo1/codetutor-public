using var cts = new CancellationTokenSource();
Task<int> work = CountAsync(cts.Token);
await Task.Yield();
cts.Cancel();
try { Console.WriteLine(await work); }
catch (OperationCanceledException) { Console.WriteLine($"cancelled, status {work.Status}"); }

using var timeout = new CancellationTokenSource(TimeSpan.FromMilliseconds(50));
try { await Task.Delay(Timeout.Infinite, timeout.Token); }
catch (TaskCanceledException) { Console.WriteLine("timed out"); }

using var caller = new CancellationTokenSource();
using var local = new CancellationTokenSource();
using var linked = CancellationTokenSource.CreateLinkedTokenSource(caller.Token, local.Token);
local.Cancel();
Console.WriteLine($"linked cancelled by either: {linked.IsCancellationRequested}");

using var race = new CancellationTokenSource();
var once = new ResultOnce();
Task<string> answer = once.WaitAsync(race.Token);
once.Complete("first result");
race.Cancel();                                   // too late: completion happened exactly once
Console.WriteLine(await answer);
Console.WriteLine($"registrations left: {once.ActiveRegistrations}");

static async Task<int> CountAsync(CancellationToken token)
{
    int count = 0;
    while (true)
    {
        token.ThrowIfCancellationRequested();
        count++;
        await Task.Yield();
    }
}

sealed class ResultOnce
{
    private readonly TaskCompletionSource<string> source = new(TaskCreationOptions.RunContinuationsAsynchronously);
    private CancellationTokenRegistration registration;
    public int ActiveRegistrations { get; private set; }

    public Task<string> WaitAsync(CancellationToken token)
    {
        registration = token.Register(() => source.TrySetCanceled(token));
        ActiveRegistrations++;
        return source.Task;
    }

    public void Complete(string result)
    {
        if (source.TrySetResult(result))
        {
            registration.Dispose();            // release the callback and what it captures
            ActiveRegistrations--;
        }
    }
}
