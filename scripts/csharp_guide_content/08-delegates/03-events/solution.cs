var t = new Thermostat();
t.TooHot += (_, reading) => Console.WriteLine($"too hot: {reading}");
t.Set(25);
t.Set(31);

class Thermostat
{
    public event EventHandler<double>? TooHot;
    public void Set(double celsius)
    {
        if (celsius > 30) TooHot?.Invoke(this, celsius);
    }
}
