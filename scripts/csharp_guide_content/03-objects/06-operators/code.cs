var a = new Vector(1, 2);
var b = new Vector(3, 4);
Console.WriteLine(a + b);
Console.WriteLine(a * 3);
Console.WriteLine(-a);
Console.WriteLine(a == new Vector(1, 2));

var total = new Accumulator();
total += 5;          // C# 14: calls the instance += operator, mutating in place
total += 7;
Console.WriteLine($"{total.Sum} after {total.Updates} in-place updates");

var temp = new Celsius(21.5);
double raw = (double)temp;
Console.WriteLine(raw);

readonly record struct Vector(double X, double Y)
{
    public static Vector operator +(Vector a, Vector b) => new(a.X + b.X, a.Y + b.Y);
    public static Vector operator *(Vector v, double k) => new(v.X * k, v.Y * k);
    public static Vector operator -(Vector v) => new(-v.X, -v.Y);
    public override string ToString() => $"({X}, {Y})";
}

class Accumulator
{
    public int Sum { get; private set; }
    public int Updates { get; private set; }
    public void operator +=(int value) { Sum += value; Updates++; }
}

readonly struct Celsius(double degrees)
{
    public double Degrees { get; } = degrees;   // static operators cannot see primary-constructor parameters
    public static explicit operator double(Celsius c) => c.Degrees;
}
