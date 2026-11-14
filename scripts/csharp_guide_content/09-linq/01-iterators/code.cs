foreach (var n in Countdown(3)) Console.Write(n + " ");
Console.WriteLine();
Console.WriteLine(string.Join(",", Fibonacci().Take(8)));

var lazy = Logged();
Console.WriteLine("created, nothing ran yet");
foreach (var x in lazy)
{
    Console.WriteLine($"got {x}");
    if (x == 2) break;
}

try { var bad = Chunked(null!, 2); Console.WriteLine("eager validation did not throw?"); }
catch (ArgumentNullException) { Console.WriteLine("validated eagerly"); }

static IEnumerable<int> Countdown(int from)
{
    for (int i = from; i > 0; i--) yield return i;
    yield return 0;
}

static IEnumerable<long> Fibonacci()
{
    long a = 0, b = 1;
    while (true)
    {
        yield return a;
        (a, b) = (b, a + b);
    }
}

static IEnumerable<int> Logged()
{
    try
    {
        for (int i = 1; i <= 5; i++)
        {
            Console.WriteLine($"producing {i}");
            yield return i;
        }
    }
    finally { Console.WriteLine("iterator cleaned up"); }
}

static IEnumerable<int[]> Chunked(IEnumerable<int> source, int size)
{
    ArgumentNullException.ThrowIfNull(source);       // runs now, not on first MoveNext
    return Iterate();
    IEnumerable<int[]> Iterate()
    {
        var chunk = new List<int>(size);
        foreach (var x in source)
        {
            chunk.Add(x);
            if (chunk.Count == size) { yield return chunk.ToArray(); chunk.Clear(); }
        }
        if (chunk.Count > 0) yield return chunk.ToArray();
    }
}
