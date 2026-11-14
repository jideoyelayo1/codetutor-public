Task<int>[] tasks = [SquareLaterAsync(2), SquareLaterAsync(3), SquareLaterAsync(4)];
int[] squares = await Task.WhenAll(tasks);
Console.WriteLine(squares.Sum());

static async Task<int> SquareLaterAsync(int n)
{
    await Task.Yield();
    return n * n;
}
