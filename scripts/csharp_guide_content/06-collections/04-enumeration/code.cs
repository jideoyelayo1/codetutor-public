var numbers = new List<int> { 1, 2, 3, 4, 5, 6 };
try
{
    foreach (var n in numbers)
        if (n % 2 == 0) numbers.Remove(n);
}
catch (InvalidOperationException e) { Console.WriteLine(e.Message); }

numbers = [1, 2, 3, 4, 5, 6];
int removed = numbers.RemoveAll(n => n % 2 == 0);
Console.WriteLine($"{removed} removed: {string.Join(",", numbers)}");

numbers = [1, 2, 3, 4, 5, 6];
for (int i = numbers.Count - 1; i >= 0; i--)
    if (numbers[i] % 3 == 0) numbers.RemoveAt(i);
Console.WriteLine(string.Join(",", numbers));

using var enumerator = numbers.GetEnumerator();
while (enumerator.MoveNext()) Console.Write($"[{enumerator.Current}]");
Console.WriteLine();
Console.WriteLine(Total(new HashSet<int> { 1, 2 }) + Total([10, 20]));

static int Total(IEnumerable<int> values)
{
    int sum = 0;
    foreach (var v in values) sum += v;
    return sum;
}
