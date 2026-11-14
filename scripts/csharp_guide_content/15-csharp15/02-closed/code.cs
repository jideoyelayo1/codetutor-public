GateState[] states = [new Closed(), new Open(50), new Open(100), new Locked("night mode")];
foreach (var s in states) Console.WriteLine(Describe(s));
Console.WriteLine(Next(new Open(50)));

static string Describe(GateState state) => state switch
{
    Closed => "closed",
    Open(100) => "fully open",
    Open(var percent) => $"{percent}% open",
    Locked(var reason) => $"locked ({reason})",
};

static GateState Next(GateState state) => state switch
{
    Closed => new Open(10),
    Open(var p) when p < 100 => new Open(Math.Min(100, p + 25)),
    Open => new Closed(),
    Locked l => l,
};

public closed record GateState;
public record Closed : GateState;
public record Open(int Percent) : GateState;
public record Locked(string Reason) : GateState;
