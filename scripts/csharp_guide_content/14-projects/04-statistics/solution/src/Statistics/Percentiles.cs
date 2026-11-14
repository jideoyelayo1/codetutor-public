using System.Numerics;

namespace Statistics;

public static class Percentiles
{
    /// <summary>Linear interpolation between closest ranks: p = 0 is the minimum, p = 100 the maximum.</summary>
    public static TResult Percentile<T, TResult>(ReadOnlySpan<T> values, double p)
        where T : INumber<T> where TResult : IFloatingPoint<TResult>
    {
        if (values.IsEmpty) throw new ArgumentException("At least one value is required.", nameof(values));
        ArgumentOutOfRangeException.ThrowIfLessThan(p, 0.0);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(p, 100.0);
        T[] sorted = values.ToArray();
        Array.Sort(sorted);
        double rank = p / 100.0 * (sorted.Length - 1);
        int lower = (int)Math.Floor(rank);
        int upper = (int)Math.Ceiling(rank);
        TResult low = TResult.CreateChecked(sorted[lower]);
        TResult high = TResult.CreateChecked(sorted[upper]);
        return low + (high - low) * TResult.CreateChecked(rank - lower);
    }
}
