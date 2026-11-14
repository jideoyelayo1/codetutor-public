var result = Enumerable.Range(1, 99_999).AsParallel()
    .Where(n => DigitSum(n) == 30)
    .OrderByDescending(n => n)
    .Take(5);
Console.WriteLine(string.Join(",", result));

static int DigitSum(int n)
{
    int sum = 0;
    for (; n > 0; n /= 10) sum += n % 10;
    return sum;
}
