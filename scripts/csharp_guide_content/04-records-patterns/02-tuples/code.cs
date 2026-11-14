int[] data = [4, 9, 1, 7];
var (min, max) = Range(data);
Console.WriteLine($"{min}..{max}");
(string Name, int Score) best = ("Ada", 97);
Console.WriteLine($"{best.Name} {best.Item2}");

int a = 1, b = 2;
(a, b) = (b, a);
Console.WriteLine($"{a} {b}");

var (_, top) = Range([3, 8]);
Console.WriteLine(top);
Console.WriteLine((1, "x") == (1, "x"));

var grid = new Dictionary<(int, int), char> { [(0, 0)] = 'S', [(2, 1)] = 'G' };
Console.WriteLine(grid[(2, 1)]);

var (x, y) = new Point(3, 4);
Console.WriteLine(x + y);

static (int Min, int Max) Range(int[] xs) => (xs.Min(), xs.Max());

class Point(int x, int y)
{
    public void Deconstruct(out int px, out int py) { px = x; py = y; }
}
