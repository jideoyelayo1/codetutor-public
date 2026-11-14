string path;
using (var temp = new TempFile())
{
    path = temp.Path;
    File.WriteAllText(path, "hello");
    Console.WriteLine($"{File.Exists(path)} {File.ReadAllText(path)}");
}
Console.WriteLine(File.Exists(path));

sealed class TempFile : IDisposable
{
    public string Path { get; } = System.IO.Path.GetTempFileName();
    private bool disposed;
    public void Dispose()
    {
        if (disposed) return;
        disposed = true;
        File.Delete(Path);
    }
}
