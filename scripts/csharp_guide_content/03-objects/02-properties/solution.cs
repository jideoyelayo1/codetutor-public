var p = new Progress();
foreach (var v in new[] { -5, 42, 250 })
{
    p.Percent = v;
    Console.WriteLine(p.Percent);
}

class Progress
{
    public int Percent
    {
        get;
        set => field = Math.Clamp(value, 0, 100);
    }
}
