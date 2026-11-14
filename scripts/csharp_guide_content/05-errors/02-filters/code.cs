using System.Runtime.CompilerServices;

foreach (var code in new[] { 404, 500 })
{
    try { Fetch(code); }
    catch (ServiceException e) when (e.Status == 404) { Console.WriteLine("not found, using default"); }
    catch (ServiceException e) { Console.WriteLine($"service failed with {e.Status}"); }
}

try { Load(); }
catch (ConfigException e)
{
    Console.WriteLine(e.Message);
    Console.WriteLine($"cause: {e.InnerException?.GetType().Name}: {e.InnerException?.Message}");
}

try { Rethrow(); }
catch (InvalidOperationException e) { Console.WriteLine(e.StackTrace!.Contains(nameof(Origin)) ? "origin preserved" : "origin lost"); }

static void Fetch(int status) => throw new ServiceException(status);

static void Load()
{
    try { int.Parse("12x"); }
    catch (FormatException e) { throw new ConfigException("Invalid port in settings", e); }
}

[MethodImpl(MethodImplOptions.NoInlining)]
static void Origin() => throw new InvalidOperationException("deep failure");

static void Rethrow()
{
    try { Origin(); }
    catch (InvalidOperationException) { throw; }
}

class ServiceException(int status) : Exception($"Service returned {status}")
{
    public int Status => status;
}

class ConfigException : Exception
{
    public ConfigException() { }
    public ConfigException(string message) : base(message) { }
    public ConfigException(string message, Exception inner) : base(message, inner) { }
}
