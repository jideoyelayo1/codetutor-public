var a = MakeAccumulator(10);
var b = MakeAccumulator(0);
a(5); b(1);
Console.WriteLine($"{a(0)} {b(0)}");

static Func<int, int> MakeAccumulator(int start)
{
    int total = start;
    return x => total += x;
}
