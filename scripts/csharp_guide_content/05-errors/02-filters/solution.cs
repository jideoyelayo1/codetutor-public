int calls = 0;
Console.WriteLine(Retry(() => ++calls < 3 ? throw new TimeoutException() : 7, 5));
Console.WriteLine($"calls: {calls}");
try { Retry(() => throw new InvalidOperationException("fatal"), 5); }
catch (InvalidOperationException e) { Console.WriteLine(e.Message); }

static int Retry(Func<int> action, int attempts)
{
    for (int i = 1; ; i++)
    {
        try { return action(); }
        catch (TimeoutException) when (i < attempts) { }
    }
}
