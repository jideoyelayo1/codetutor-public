using Statistics;

namespace Statistics.Tests;

public class StatsTests
{
    [Fact]
    public void MeanWorksForIntsAndDecimals()
    {
        Assert.Equal(2.5, Stats.Mean<int, double>([1, 2, 3, 4]));
        Assert.Equal(0.2m, Stats.Mean<decimal, decimal>([0.1m, 0.3m]));
    }

    [Fact]
    public void MeanDoesNotOverflowNarrowInputs()
    {
        Assert.Equal(150.0, Stats.Mean<byte, double>([200, 100]));
        Assert.Equal(int.MaxValue, Stats.Mean<int, double>([int.MaxValue, int.MaxValue]));
    }

    [Theory]
    [InlineData(new[] { 5.0 }, 5.0)]
    [InlineData(new[] { 3.0, 1.0, 2.0 }, 2.0)]
    [InlineData(new[] { 4.0, 1.0, 3.0, 2.0 }, 2.5)]
    public void MedianHandlesOddAndEvenCounts(double[] values, double expected) =>
        Assert.Equal(expected, Stats.Median<double, double>(values));

    [Fact]
    public void VarianceOfConstantIsZero() => Assert.Equal(0.0, Stats.Variance<int, double>([7, 7, 7]));

    [Fact]
    public void VarianceIsPopulationVariance() => Assert.Equal(4.0, Stats.Variance<int, double>([2, 4, 4, 4, 5, 5, 7, 9]));

    [Fact]
    public void HistogramCountsSortedByValue() =>
        Assert.Equal([new(1, 2), new(3, 1)], Stats.Histogram([3, 1, 1]));

    [Fact]
    public void EmptyInputIsRejected() => Assert.Throws<ArgumentException>(() => Stats.Mean<int, double>([]));
}
