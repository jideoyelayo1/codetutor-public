var log = new List<string>();

async Task StepsAsync(Task wait)
{
    log.Add("before await (runs synchronously)");
    await wait;
    log.Add("after await");
}

Task pending = StepsAsync(Task.CompletedTask);   // already complete: no suspension
log.Add($"returned, completed={pending.IsCompleted}");
var gate = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
Task suspended = StepsAsync(gate.Task);
log.Add($"returned, completed={suspended.IsCompleted}");
gate.SetResult();
await suspended;
Console.WriteLine(string.Join("\n", log));

Task<int> failing = FailAsync();
Console.WriteLine($"exception stored, status {failing.Status}");
try { await failing; }
catch (InvalidOperationException e) { Console.WriteLine($"rethrown at await: {e.Message}"); }

int value = await ComputeAsync().ConfigureAwait(false);
Console.WriteLine($"ConfigureAwait(false) result {value}");
Console.WriteLine(SynchronizationContext.Current is null ? "console apps have no SynchronizationContext" : "context present");

static async Task<int> FailAsync()
{
    await Task.CompletedTask;   // completes synchronously, so the task is already Faulted when returned
    throw new InvalidOperationException("failed inside the task");
}

static async Task<int> ComputeAsync()
{
    await Task.Yield();
    return 7;
}
