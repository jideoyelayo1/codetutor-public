var wallet = new Money(10m);
var copy = wallet;
copy = copy.Add(5m);
Console.WriteLine($"{wallet.Amount} {copy.Amount}");

readonly record struct Money(decimal Amount)
{
    public Money Add(decimal extra) => new(Amount + extra);
}
