long sequential = 0;
for (int i = 1; i <= 1_000_000; i++) sequential += i % 7;

long parallel = 0;
Parallel.For(1, 1_000_001,
    () => 0L,
    (i, _, local) => local + i % 7,
    local => Interlocked.Add(ref parallel, local));
Console.WriteLine($"{sequential} {parallel == sequential}");

var squares = Enumerable.Range(1, 10).AsParallel().AsOrdered().Select(n => n * n).ToArray();
Console.WriteLine(string.Join(",", squares));

int primes = Enumerable.Range(2, 50_000).AsParallel().WithDegreeOfParallelism(4).Count(IsPrime);
Console.WriteLine(primes);

try
{
    Parallel.For(0, 10, i => { if (i == 3 || i == 7) throw new InvalidOperationException($"item {i}"); });
}
catch (AggregateException e)
{
    Console.WriteLine($"failures collected: {e.InnerExceptions.Count >= 1}");
}

using var cts = new CancellationTokenSource();
cts.Cancel();
try { Parallel.For(0, 100, new ParallelOptions { CancellationToken = cts.Token }, _ => { }); }
catch (OperationCanceledException) { Console.WriteLine("parallel loop cancelled"); }

static bool IsPrime(int n)
{
    for (int d = 2; d * d <= n; d++) if (n % d == 0) return false;
    return true;
}
