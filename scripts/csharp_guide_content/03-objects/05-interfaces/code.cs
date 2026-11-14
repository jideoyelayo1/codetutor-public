IShape[] shapes = [new Circle(1), new Rect(2, 3)];
foreach (var s in shapes) Console.WriteLine($"{s.Name}: {s.Area():F1}");

object thing = shapes[1];
if (thing is Rect r) Console.WriteLine($"rect {r.Width}x{r.Height}");
Console.WriteLine((thing as Circle) is null);

var report = new Report();
Console.WriteLine(((IPrintable)report).Print());
Console.WriteLine(((IExportable)report).Print());
ILogger logger = new ConsoleLogger();
logger.Log("started");
logger.LogError("disk full");

interface IShape
{
    double Area();
    string Name => GetType().Name.ToLowerInvariant();   // default implementation
}
sealed class Circle(double r) : IShape { public double Area() => Math.PI * r * r; }
sealed class Rect(double w, double h) : IShape
{
    public double Width => w;
    public double Height => h;
    public double Area() => w * h;
    public string Name => "rectangle";
}

interface IPrintable { string Print(); }
interface IExportable { string Print(); }
class Report : IPrintable, IExportable
{
    string IPrintable.Print() => "printed";
    string IExportable.Print() => "exported";
}

interface ILogger
{
    void Log(string message);
    void LogError(string message) => Log("ERROR " + message);
}
class ConsoleLogger : ILogger { public void Log(string message) => Console.WriteLine(message); }
