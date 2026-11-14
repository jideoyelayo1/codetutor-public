int count = 0, total = 0;
while (Console.ReadLine() is string line)
{
    line = line.Trim();
    if (line.Length == 0) continue;
    if (!int.TryParse(line, out int value))
    {
        Console.Error.WriteLine($"skipping '{line}'");
        continue;
    }
    Console.WriteLine($"read {value}");
    count++;
    total += value;
}
Console.WriteLine($"count {count}, total {total}");
