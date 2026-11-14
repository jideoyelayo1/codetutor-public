var boiling = new Temperature(100);
Console.WriteLine(boiling.Fahrenheit);
Console.WriteLine(Temperature.FromFahrenheit(212).Celsius);

class Temperature(double celsius)
{
    public double Celsius { get; } = celsius;
    public double Fahrenheit => Celsius * 9 / 5 + 32;
    public static Temperature FromFahrenheit(double f) => new((f - 32) * 5 / 9);
}
