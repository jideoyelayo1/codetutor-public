var (count, mean) = Stats([2, 4, 9]);
Console.WriteLine($"{count} values, mean {mean:F1}");

static (int Count, double Mean) Stats(int[] xs) => (xs.Length, xs.Length == 0 ? 0 : xs.Average());
