var timeline = new List<string>();

async Task<int> FetchAsync(string name, int value, TaskCompletionSource gate)
{
    timeline.Add($"start {name}");
    await gate.Task;                   // waits without blocking a thread
    timeline.Add($"end {name}");
    return value;
}

var gateA = new TaskCompletionSource();
var gateB = new TaskCompletionSource();
Task<int> a = FetchAsync("a", 1, gateA);   // both start before either finishes
Task<int> b = FetchAsync("b", 2, gateB);
timeline.Add("both started");
gateB.SetResult();
gateA.SetResult();
int[] results = await Task.WhenAll(a, b);
Console.WriteLine(string.Join(" > ", timeline));
Console.WriteLine(results.Sum());

int cpu = await Task.Run(() => Enumerable.Range(1, 100).Sum());
Console.WriteLine(cpu);

string text = await ReadAsync();
Console.WriteLine(text);

static async Task<string> ReadAsync()
{
    string path = Path.GetTempFileName();
    try
    {
        await File.WriteAllTextAsync(path, "async I/O");
        return await File.ReadAllTextAsync(path);
    }
    finally { File.Delete(path); }
}
