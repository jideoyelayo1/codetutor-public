const int PerThread = 100_000;
int unsafeCount = 0, safeCount = 0;
var threads = Enumerable.Range(0, 4).Select(_ => new Thread(() =>
{
    for (int i = 0; i < PerThread; i++)
    {
        unsafeCount++;                          // racy read-modify-write
        Interlocked.Increment(ref safeCount);   // atomic
    }
})).ToList();
threads.ForEach(t => t.Start());
threads.ForEach(t => t.Join());
Console.WriteLine($"interlocked: {safeCount}");
Console.WriteLine($"racy count is at most the true total: {unsafeCount <= safeCount}");

int[] partials = new int[4];
Parallel.For(0, 4, worker =>
{
    int local = 0;                              // no sharing inside the loop
    for (int i = 0; i < PerThread; i++) local++;
    partials[worker] = local;
});
Console.WriteLine($"per-thread totals combined: {partials.Sum()}");

int flag = 0;
bool firstWins = Interlocked.CompareExchange(ref flag, 1, 0) == 0;
bool secondWins = Interlocked.CompareExchange(ref flag, 1, 0) == 0;
Console.WriteLine($"only one initializer: {firstWins} {secondWins}");

var config = new Config("v1");
var reader = Task.Run(() => Volatile.Read(ref config).Version);
Interlocked.Exchange(ref config, config with { Version = "v2" });   // publish a new immutable snapshot
Console.WriteLine($"reader saw a whole snapshot: {(await reader) is "v1" or "v2"}");
Console.WriteLine(config.Version);

record Config(string Version);
