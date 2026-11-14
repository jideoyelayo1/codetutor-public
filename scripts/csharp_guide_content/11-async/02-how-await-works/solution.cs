try
{
    Task t = ValidateAndDelayAsync(-1);
    Console.WriteLine("no exception yet");
    await t;
}
catch (ArgumentOutOfRangeException) { Console.WriteLine("thrown at the call site"); }
await ValidateAndDelayAsync(1);
Console.WriteLine("valid call completed");

static Task ValidateAndDelayAsync(int ms)
{
    ArgumentOutOfRangeException.ThrowIfNegative(ms);
    return Core();
    async Task Core() => await Task.Delay(ms);
}
