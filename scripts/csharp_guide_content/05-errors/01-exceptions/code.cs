Console.WriteLine(Divide(10, 2));
Console.WriteLine(Divide(1, 0));
Console.WriteLine(ParseAge("42"));
Console.WriteLine(ParseAge("old"));
Console.WriteLine(ParseAge("-5"));
Console.WriteLine(Steps());

static string Divide(int a, int b)
{
    try
    {
        return (a / b).ToString();
    }
    catch (DivideByZeroException)
    {
        return "cannot divide by zero";
    }
    finally
    {
        Console.Write("[finally] ");
    }
}

static string ParseAge(string text)
{
    try
    {
        int age = int.Parse(text);
        if (age < 0) throw new ArgumentOutOfRangeException(nameof(text), age, "Age cannot be negative.");
        return $"age {age}";
    }
    catch (FormatException)
    {
        return $"'{text}' is not a number";
    }
    catch (ArgumentOutOfRangeException e)
    {
        return $"rejected {e.ActualValue}";
    }
}

static string Steps()
{
    var log = new List<string>();
    try
    {
        try { log.Add("work"); throw new InvalidOperationException("inner"); }
        finally { log.Add("cleanup"); }
    }
    catch (InvalidOperationException e) { log.Add("caught " + e.Message); }
    return string.Join(" > ", log);
}
