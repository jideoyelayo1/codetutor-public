using System.Globalization;
using Statistics;

var numbers = new List<double>();
int lineNumber = 0;
while (Console.ReadLine() is string line)
{
    lineNumber++;
    if (string.IsNullOrWhiteSpace(line)) continue;
    if (!double.TryParse(line, NumberStyles.Float, CultureInfo.InvariantCulture, out double value))
    {
        Console.Error.WriteLine($"line {lineNumber}: not a number: {line.Trim()}");
        return 1;
    }
    numbers.Add(value);
}
if (numbers.Count == 0)
{
    Console.Error.WriteLine("no input");
    return 1;
}
ReadOnlySpan<double> data = [.. numbers];
Console.WriteLine(FormattableString.Invariant($"count {data.Length}"));
Console.WriteLine(FormattableString.Invariant($"mean {Stats.Mean<double, double>(data):F2}"));
Console.WriteLine(FormattableString.Invariant($"median {Stats.Median<double, double>(data):F2}"));
Console.WriteLine(FormattableString.Invariant($"stddev {Math.Sqrt(Stats.Variance<double, double>(data)):F2}"));
return 0;
