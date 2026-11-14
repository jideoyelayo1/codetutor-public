using System.Numerics;

Console.WriteLine(Max<int>([3, 9, 2]));
Console.WriteLine(Max<double>([1.5, -2.0]));

static T Max<T>(ReadOnlySpan<T> values) where T : INumber<T>
{
    if (values.IsEmpty) throw new ArgumentException("No values.", nameof(values));
    T best = values[0];
    foreach (var v in values) best = T.Max(best, v);
    return best;
}
