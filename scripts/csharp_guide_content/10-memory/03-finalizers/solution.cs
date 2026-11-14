using System.Runtime.InteropServices;

var pinned = new Pinned(new byte[4]);
using (pinned)
{
    Console.WriteLine(pinned.IsAllocated);
}
Console.WriteLine(pinned.IsAllocated);

// Forgotten Dispose: the finalizer frees the handle, so the array becomes collectable.
WeakReference array = AbandonPinned();
GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect();
Console.WriteLine($"array collected after forgotten Dispose: {!array.IsAlive}");

[System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
static WeakReference AbandonPinned()
{
    var data = new byte[4];
    _ = new Pinned(data);
    return new WeakReference(data);
}

sealed class Pinned(byte[] data) : IDisposable
{
    private GCHandle handle = GCHandle.Alloc(data, GCHandleType.Pinned);
    public bool IsAllocated => handle.IsAllocated;
    // The GC never frees a pinned handle, so a forgotten Dispose needs this finalizer fallback.
    ~Pinned() => Free();
    public void Dispose()
    {
        Free();
        GC.SuppressFinalize(this);
    }
    private void Free()
    {
        if (handle.IsAllocated) handle.Free();
    }
}
