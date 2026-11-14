int sum = 0;
await foreach (var n in NumbersAsync(6)) if (n % 2 == 0) sum += n;
Console.WriteLine(sum);
var evens = await NumbersAsync(6).Where(n => n % 2 == 0).ToListAsync();
Console.WriteLine(evens.Sum());

static async IAsyncEnumerable<int> NumbersAsync(int count)
{
    for (int i = 1; i <= count; i++)
    {
        await Task.Yield();
        yield return i;
    }
}
