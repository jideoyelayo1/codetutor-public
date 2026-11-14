using System.Numerics;

Console.WriteLine(Sum([1, 2, 3]));
Console.WriteLine(Sum([0.5, 0.25]));
Console.WriteLine(Sum([1.1m, 2.2m]));
Console.WriteLine(Mean<int, double>([1, 2, 4]));
Console.WriteLine(ParseAll<int>("4,5,6").Sum());
Console.WriteLine(Sum([new Money(5), new Money(7)]));
Console.WriteLine(byte.CreateSaturating(300) + " " + byte.CreateTruncating(300));
try { Console.WriteLine(byte.CreateChecked(300)); }
catch (OverflowException) { Console.WriteLine("300 does not fit in a byte"); }

static T Sum<T>(IEnumerable<T> values) where T : IAdditionOperators<T, T, T>, IAdditiveIdentity<T, T>
{
    T total = T.AdditiveIdentity;
    foreach (var v in values) total += v;
    return total;
}

// Convert before adding: Sum in T would wrap for narrow inputs (two bytes of 200) before the conversion.
static TResult Mean<T, TResult>(IReadOnlyList<T> values) where T : INumber<T> where TResult : INumber<TResult>
    => Sum(values.Select(TResult.CreateChecked)) / TResult.CreateChecked(values.Count);

static IEnumerable<T> ParseAll<T>(string csv) where T : IParsable<T>
{
    foreach (var part in csv.Split(',')) yield return T.Parse(part, null);
}

readonly record struct Money(decimal Amount) : IAdditionOperators<Money, Money, Money>, IAdditiveIdentity<Money, Money>
{
    public static Money AdditiveIdentity => new(0m);
    public static Money operator +(Money left, Money right) => new(left.Amount + right.Amount);
}
