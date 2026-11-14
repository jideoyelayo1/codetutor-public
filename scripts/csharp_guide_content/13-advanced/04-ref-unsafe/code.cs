int[] scores = [10, 20, 30];
ref int middle = ref scores[1];
middle += 5;
Console.WriteLine(string.Join(",", scores));

ref int largest = ref Largest(scores);
largest = 0;                               // writes into the array
Console.WriteLine(string.Join(",", scores));

var buffer = new Buffer3();      // a class: it may return refs to its own fields
buffer[1] = 7;
Console.WriteLine(buffer[1]);

Span<int> local = stackalloc int[4];
Console.WriteLine(Fill(local, 9));

unsafe
{
    int value = 41;
    int* pointer = &value;
    *pointer += 1;
    Console.WriteLine(value);
    fixed (int* first = scores)
    {
        Console.WriteLine(*(first + 2));     // pointer arithmetic over pinned memory
    }
    delegate*<int, int> square = &Square;
    Console.WriteLine(square(12));
    Console.WriteLine(sizeof(Pair));
}

static ref int Largest(int[] values)
{
    int index = 0;
    for (int i = 1; i < values.Length; i++) if (values[i] > values[index]) index = i;
    return ref values[index];
}

static int Fill(scoped Span<int> target, int value)
{
    target.Fill(value);
    int sum = 0;
    foreach (var v in target) sum += v;
    return sum;
}

static int Square(int x) => x * x;

readonly record struct Pair(int A, int B);

sealed class Buffer3
{
    private int a, b, c;
    public ref int this[int index]
    {
        get
        {
            switch (index)
            {
                case 0: return ref a;
                case 1: return ref b;
                case 2: return ref c;
                default: throw new IndexOutOfRangeException();
            }
        }
    }
}
