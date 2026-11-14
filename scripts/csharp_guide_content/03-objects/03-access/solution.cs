var c = new Counter();
Console.WriteLine($"{c.Increment(5)} {c.Value}");
Console.WriteLine($"{c.Increment(-1)} {c.Value}");

class Counter
{
    public int Value { get; private set; }
    public bool Increment(int by)
    {
        if (by <= 0) return false;
        Value += by;
        return true;
    }
}
