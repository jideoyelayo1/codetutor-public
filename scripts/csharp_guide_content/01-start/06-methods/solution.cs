MinMax(out int min, out int max, 4, 9, 1, 7);
Console.WriteLine($"min {min}, max {max}");

static void MinMax(out int min, out int max, params int[] values)
{
    if (values.Length == 0) throw new ArgumentException("At least one value is required.", nameof(values));
    min = max = values[0];
    foreach (int v in values)
    {
        if (v < min) min = v;
        if (v > max) max = v;
    }
}
