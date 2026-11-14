var count = 3;
Console.WriteLine(count.GetType());
double d = 0.1 + 0.2;
decimal m = 0.1m + 0.2m;
Console.WriteLine(d.ToString("R"));
Console.WriteLine(m);
Console.WriteLine((int)3.9);
int big = int.MaxValue;
big++;
Console.WriteLine(big);
try
{
    int max = int.MaxValue;
    Console.WriteLine(checked(max + 1));
}
catch (OverflowException)
{
    Console.WriteLine("Overflow detected");
}
