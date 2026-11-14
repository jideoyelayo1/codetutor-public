int[] data = [10, 20, 30, 40, 50];
Span<int> middle = data.AsSpan(1, 3);
middle[0] = 99;                       // writes through to the array: no copy
Console.WriteLine(string.Join(",", data));
Console.WriteLine(middle[^1]);

ReadOnlySpan<char> line = "name=Ada;age=36";
int split = line.IndexOf(';');
ReadOnlySpan<char> first = line[..split];
ReadOnlySpan<char> value = first[(first.IndexOf('=') + 1)..];
Console.WriteLine(value.ToString());
Console.WriteLine(int.Parse(line[(line.LastIndexOf('=') + 1)..]));

Span<byte> scratch = stackalloc byte[4];
scratch.Fill(7);
Console.WriteLine(scratch.Length + " " + scratch[3]);

Memory<int> memory = data.AsMemory(2);
Console.WriteLine(Sum(memory.Span));

int[] measurements = [3, 1, 2];
Console.WriteLine(measurements.Total());     // C# 14: array -> ReadOnlySpan<int> for an extension call
Console.WriteLine(Sum(measurements));

static int Sum(ReadOnlySpan<int> values)
{
    int total = 0;
    foreach (var v in values) total += v;
    return total;
}

static class SpanExtensions
{
    public static int Total(this ReadOnlySpan<int> values)
    {
        int total = 0;
        foreach (var v in values) total += v;
        return total;
    }
}
