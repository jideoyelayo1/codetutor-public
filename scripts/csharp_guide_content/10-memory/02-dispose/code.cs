using (var first = new Resource("block"))
{
    first.Use();
}

Run();

var owner = new Owner();
owner.Dispose();
owner.Dispose();                 // idempotent: nothing happens
try { owner.Work(); }
catch (ObjectDisposedException e) { Console.WriteLine($"{e.ObjectName} used after dispose"); }

try
{
    using var failing = new Resource("exception path");
    throw new InvalidOperationException("boom");
}
catch (InvalidOperationException) { Console.WriteLine("caught after dispose ran"); }

static void Run()
{
    using var a = new Resource("a");
    using var b = new Resource("b");
    Console.WriteLine("end of Run body");
}

sealed class Resource(string name) : IDisposable
{
    public void Use() => Console.WriteLine($"using {name}");
    public void Dispose() => Console.WriteLine($"disposed {name}");
}

sealed class Owner : IDisposable
{
    private readonly Resource inner = new("owned");
    private bool disposed;
    public void Work()
    {
        ObjectDisposedException.ThrowIf(disposed, this);
        inner.Use();
    }
    public void Dispose()
    {
        if (disposed) return;
        disposed = true;
        inner.Dispose();
    }
}
