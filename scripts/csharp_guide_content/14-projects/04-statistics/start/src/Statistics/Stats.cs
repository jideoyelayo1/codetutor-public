using System.Numerics;

namespace Statistics;

public static class Stats
{
    public static TResult Mean<T, TResult>(ReadOnlySpan<T> values)
        where T : INumber<T> where TResult : IFloatingPoint<TResult>
    {
        if (values.IsEmpty) throw new ArgumentException("At least one value is required.", nameof(values));
        // Sum in TResult: summing in T would overflow narrow inputs (two bytes of 200 wrap) before conversion.
        TResult sum = TResult.Zero;
        foreach (var v in values) sum += TResult.CreateChecked(v);
        return sum / TResult.CreateChecked(values.Length);
    }

    public static TResult Variance<T, TResult>(ReadOnlySpan<T> values)
        where T : INumber<T> where TResult : IFloatingPoint<TResult>
    {
        if (values.IsEmpty) throw new ArgumentException("At least one value is required.", nameof(values));
        TResult mean = Mean<T, TResult>(values);
        TResult squares = TResult.Zero;
        foreach (var v in values)
        {
            TResult d = TResult.CreateChecked(v) - mean;
            squares += d * d;
        }
        return squares / TResult.CreateChecked(values.Length);
    }

    /// <summary>Middle value of the sorted input; the mean of the two middle values for even counts.</summary>
    public static TResult Median<T, TResult>(ReadOnlySpan<T> values)
        where T : INumber<T> where TResult : IFloatingPoint<TResult>
    {
        if (values.IsEmpty) throw new ArgumentException("At least one value is required.", nameof(values));
        T[] sorted = values.ToArray();
        Array.Sort(sorted);
        int middle = sorted.Length / 2;
        return sorted.Length % 2 == 1
            ? TResult.CreateChecked(sorted[middle])
            : (TResult.CreateChecked(sorted[middle - 1]) + TResult.CreateChecked(sorted[middle])) / TResult.CreateChecked(2);
    }

    public static IReadOnlyList<KeyValuePair<T, int>> Histogram<T>(IEnumerable<T> values) where T : INumber<T> =>
        values.CountBy(v => v).OrderBy(pair => pair.Key).ToList();
}
