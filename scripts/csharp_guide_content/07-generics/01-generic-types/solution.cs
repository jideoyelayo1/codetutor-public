var p = new Pair<int, string>(1, "one");
Console.WriteLine(p.Swap());
Console.WriteLine(FirstOrFallback(new List<string>(), "none"));
Console.WriteLine(FirstOrFallback([5, 6], -1));

static T FirstOrFallback<T>(IEnumerable<T> xs, T fallback)
{
    foreach (var x in xs) return x;
    return fallback;
}

record Pair<TFirst, TSecond>(TFirst First, TSecond Second)
{
    public Pair<TSecond, TFirst> Swap() => new(Second, First);
}
