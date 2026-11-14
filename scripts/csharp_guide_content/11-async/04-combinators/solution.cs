var t1 = Task.FromException<int>(new Exception("down"));
var t2 = Task.FromResult(42);
Console.WriteLine(await FirstSuccessfulAsync([t1, t2]));
try { await FirstSuccessfulAsync([t1]); }
catch (InvalidOperationException e) { Console.WriteLine(e.Message); }

static async Task<int> FirstSuccessfulAsync(IEnumerable<Task<int>> tasks)
{
    await foreach (var task in Task.WhenEach(tasks))
        if (task.IsCompletedSuccessfully) return task.Result;
    throw new InvalidOperationException("Every task failed.");
}
