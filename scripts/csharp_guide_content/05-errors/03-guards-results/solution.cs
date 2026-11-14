foreach (var (a, b) in new[] { (9, 3), (1, 0) })
    Console.WriteLine(TryDivide(a, b, out int q) ? $"{a}/{b} = {q}" : $"{a}/{b} is undefined");

static bool TryDivide(int a, int b, out int quotient)
{
    quotient = 0;
    if (b == 0) return false;
    quotient = a / b;
    return true;
}
