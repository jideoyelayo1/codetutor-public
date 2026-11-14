Console.WriteLine(Clamp(15, 0, 10));
Console.WriteLine(Clamp("m", "c", "k"));
Console.WriteLine(Clamp(5, 0, 10));

static T Clamp<T>(T value, T min, T max) where T : IComparable<T>
{
    if (min.CompareTo(max) > 0) throw new ArgumentException("min must not exceed max");
    if (value.CompareTo(min) < 0) return min;
    if (value.CompareTo(max) > 0) return max;
    return value;
}
