string? empty = "   ";
Console.WriteLine(empty.IsBlank);
Console.WriteLine("Ada".IsBlank);
Console.WriteLine("hello world".WordCount());

int[] values = [3, 1, 2];
Console.WriteLine(values.IsEmpty);
Console.WriteLine(values.SecondLargest());

Console.WriteLine(Temperature.Freezing);
Console.WriteLine(new Temperature(20) + new Temperature(1.5));

static class TextExtensions
{
    // Classic extension method.
    public static int WordCount(this string text) => text.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length;

    // C# 14 extension block with an extension property.
    extension(string? text)
    {
        public bool IsBlank => string.IsNullOrWhiteSpace(text);
    }
}

static class SequenceExtensions
{
    extension<T>(IEnumerable<T> source) where T : IComparable<T>
    {
        public bool IsEmpty => !source.Any();
        public T SecondLargest() => source.OrderDescending().Skip(1).First();
    }
}

record Temperature(double Celsius);

static class TemperatureExtensions
{
    extension(Temperature)
    {
        public static Temperature Freezing => new(0);
        public static Temperature operator +(Temperature a, Temperature b) => new(a.Celsius + b.Celsius);
    }
}
