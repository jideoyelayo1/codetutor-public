using Statistics;

namespace Statistics.Tests;

public class PercentileTests
{
    [Theory]
    [InlineData(0.0, 1.0)]
    [InlineData(50.0, 2.5)]
    [InlineData(100.0, 4.0)]
    [InlineData(25.0, 1.75)]
    public void InterpolatesBetweenRanks(double p, double expected) =>
        Assert.Equal(expected, Percentiles.Percentile<int, double>([4, 1, 3, 2], p), 10);

    [Fact]
    public void FiftiethPercentileMatchesMedian() =>
        Assert.Equal(Stats.Median<int, double>([9, 1, 5]), Percentiles.Percentile<int, double>([9, 1, 5], 50));

    [Fact]
    public void RejectsOutOfRangePercent() =>
        Assert.Throws<ArgumentOutOfRangeException>(() => Percentiles.Percentile<int, double>([1], 101));
}
