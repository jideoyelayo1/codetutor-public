var a = new Money(5m, "USD");
var b = new Money(7m, "USD");
Console.WriteLine(a + b);
try { Console.WriteLine(a + new Money(1m, "EUR")); }
catch (InvalidOperationException e) { Console.WriteLine(e.Message); }

readonly record struct Money(decimal Amount, string Currency)
{
    public static Money operator +(Money left, Money right) =>
        left.Currency == right.Currency
            ? new(left.Amount + right.Amount, left.Currency)
            : throw new InvalidOperationException($"Cannot add {left.Currency} to {right.Currency}");
    public override string ToString() => $"{Amount} {Currency}";
}
