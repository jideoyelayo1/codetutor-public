using System.Runtime.CompilerServices;

var weak = Cache();
GC.Collect();
Console.WriteLine($"cached: {weak.IsAlive}");
Holder.Items.Clear();
GC.Collect();
Console.WriteLine($"after clear: {weak.IsAlive}");

[MethodImpl(MethodImplOptions.NoInlining)]
static WeakReference Cache()
{
    var item = new byte[64];
    Holder.Items.Add(item);
    return new WeakReference(item);
}

static class Holder { public static readonly List<object> Items = []; }
