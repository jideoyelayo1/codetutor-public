Result ok = 42;
Result failed = new Error("disk full");
Result cancelled = new Cancelled();
foreach (var r in new[] { ok, failed, cancelled }) Console.WriteLine(Describe(r));

Shape[] shapes = [new Circle(1), new Square(2), new Circle(0.5)];
Console.WriteLine(shapes.Sum(Area).ToString("F2"));

static string Describe(Result result) => result switch
{
    int value => $"ok: {value}",
    Error e => $"error: {e.Message}",
    Cancelled => "cancelled",
};

static double Area(Shape shape) => shape switch
{
    Circle c => Math.PI * c.Radius * c.Radius,
    Square s => s.Side * s.Side,
};

public record Error(string Message);
public record Cancelled;
public union Result(int, Error, Cancelled);

public record Circle(double Radius);
public record Square(double Side);
public union Shape(Circle, Square);
