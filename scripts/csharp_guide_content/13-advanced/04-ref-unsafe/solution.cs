int[] values = [5, -2, -7];
FirstNegative(values) = 0;
Console.WriteLine(string.Join(",", values));

static ref int FirstNegative(Span<int> values)
{
    for (int i = 0; i < values.Length; i++)
        if (values[i] < 0) return ref values[i];
    throw new InvalidOperationException("No negative value.");
}
