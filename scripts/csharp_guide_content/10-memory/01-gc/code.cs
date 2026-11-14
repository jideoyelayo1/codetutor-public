using System.Runtime.CompilerServices;

var fresh = new object();
Console.WriteLine($"new object generation: {GC.GetGeneration(fresh)}");
GC.Collect();
Console.WriteLine($"after one collection: {GC.GetGeneration(fresh)}");
GC.Collect();
Console.WriteLine($"after two collections: {GC.GetGeneration(fresh)}");
GC.KeepAlive(fresh);

var big = new byte[100_000];
Console.WriteLine($"large array generation: {GC.GetGeneration(big)}");

WeakReference cycle = MakeCycle();
GC.Collect();
Console.WriteLine($"unreachable cycle collected: {!cycle.IsAlive}");

int[] values = [1, 2, 3];
Warm(values);
long before = GC.GetAllocatedBytesForCurrentThread();
int sum = SumNoAlloc(values);
long noAlloc = GC.GetAllocatedBytesForCurrentThread() - before;
before = GC.GetAllocatedBytesForCurrentThread();
string text = string.Join(",", Enumerable.Range(0, 100));
long withAlloc = GC.GetAllocatedBytesForCurrentThread() - before;
Console.WriteLine($"sum {sum}: zero allocations={noAlloc == 0}; join allocated={withAlloc > 0}");

static void Warm(int[] values) { SumNoAlloc(values); GC.GetAllocatedBytesForCurrentThread(); }
static int SumNoAlloc(ReadOnlySpan<int> values)
{
    int total = 0;
    foreach (var v in values) total += v;
    return total;
}

[MethodImpl(MethodImplOptions.NoInlining)]
static WeakReference MakeCycle()
{
    var a = new Node();
    var b = new Node { Next = a };
    a.Next = b;                      // a <-> b reference each other
    return new WeakReference(a);
}

class Node { public Node? Next; }
