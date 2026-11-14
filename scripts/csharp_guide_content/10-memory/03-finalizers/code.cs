using System.Runtime.CompilerServices;

Forget();
GC.Collect();
GC.WaitForPendingFinalizers();
Console.WriteLine($"finalized without Dispose: {NativeBuffer.FinalizedCount}");

using (var buffer = new NativeBuffer(16))
{
    buffer.Write(0, 42);
    Console.WriteLine(buffer.Read(0));
}
GC.Collect();
GC.WaitForPendingFinalizers();
Console.WriteLine($"finalized after Dispose: {NativeBuffer.FinalizedCount}");

using (var derived = new LoggingBuffer(8)) { }

[MethodImpl(MethodImplOptions.NoInlining)]
static void Forget() => _ = new NativeBuffer(8);

class NativeBuffer : IDisposable
{
    public static int FinalizedCount;
    private IntPtr memory;
    public NativeBuffer(int bytes) => memory = System.Runtime.InteropServices.Marshal.AllocHGlobal(bytes);
    public void Write(int offset, byte value) => System.Runtime.InteropServices.Marshal.WriteByte(memory, offset, value);
    public byte Read(int offset) => System.Runtime.InteropServices.Marshal.ReadByte(memory, offset);

    public void Dispose()
    {
        Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (memory == IntPtr.Zero) return;
        System.Runtime.InteropServices.Marshal.FreeHGlobal(memory);   // unmanaged: safe in both paths
        memory = IntPtr.Zero;
    }

    ~NativeBuffer()
    {
        Interlocked.Increment(ref FinalizedCount);
        Dispose(disposing: false);
    }
}

sealed class LoggingBuffer(int bytes) : NativeBuffer(bytes)
{
    protected override void Dispose(bool disposing)
    {
        if (disposing) Console.WriteLine("derived cleanup of managed state");
        base.Dispose(disposing);
    }
}
