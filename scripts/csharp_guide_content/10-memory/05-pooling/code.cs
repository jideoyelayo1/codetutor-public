using System.Buffers;

Console.WriteLine(Checksum("hello world"u8));
Console.WriteLine(Repeat('-', 5));
Console.WriteLine(FormatPair(7, 42));

byte[] rented = ArrayPool<byte>.Shared.Rent(10);
Console.WriteLine($"asked 10, got at least 10: {rented.Length >= 10}");
ArrayPool<byte>.Shared.Return(rented);

Warm();
long before = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) Checksum("hello world"u8);
Console.WriteLine($"pooled checksum loop allocated nothing: {GC.GetAllocatedBytesForCurrentThread() - before == 0}");

static void Warm() { Checksum("x"u8); GC.GetAllocatedBytesForCurrentThread(); }

static int Checksum(ReadOnlySpan<byte> input)
{
    const int StackLimit = 256;
    byte[]? pooled = null;
    Span<byte> buffer = input.Length <= StackLimit
        ? stackalloc byte[StackLimit]
        : (pooled = ArrayPool<byte>.Shared.Rent(input.Length));
    try
    {
        Span<byte> work = buffer[..input.Length];
        input.CopyTo(work);
        int sum = 0;
        foreach (var b in work) sum = (sum * 31 + b) & 0xFFFF;
        return sum;
    }
    finally
    {
        if (pooled is not null) ArrayPool<byte>.Shared.Return(pooled);
    }
}

static string Repeat(char c, int count) => string.Create(count, c, static (span, ch) => span.Fill(ch));

static string FormatPair(int a, int b) =>
    string.Create(null, stackalloc char[32], $"{a}:{b}");
