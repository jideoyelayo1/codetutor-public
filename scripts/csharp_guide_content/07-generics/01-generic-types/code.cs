var ints = new Stack2<int>();
ints.Push(1); ints.Push(2);
Console.WriteLine(ints.Pop() + ints.Pop());
var words = new Stack2<string>();
words.Push("hi");
Console.WriteLine(words.Peek().ToUpperInvariant());
Console.WriteLine(words.PeekOrDefault() + "|" + new Stack2<int>().PeekOrDefault());

Console.WriteLine(Max(3, 7));
Console.WriteLine(Max("pear", "apple"));
Console.WriteLine(Describe(42) + " " + Describe("x") + " " + Describe(new List<int>()));
Counter<int>.Count++; Counter<int>.Count++; Counter<string>.Count++;
Console.WriteLine($"{Counter<int>.Count} {Counter<string>.Count}");

static T Max<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b) >= 0 ? a : b;
static string Describe<T>(T _) => typeof(T).Name;

class Stack2<T>
{
    private readonly List<T> items = [];
    public void Push(T item) => items.Add(item);
    public T Pop()
    {
        if (items.Count == 0) throw new InvalidOperationException("empty");
        T item = items[^1];
        items.RemoveAt(items.Count - 1);
        return item;
    }
    public T Peek() => items.Count > 0 ? items[^1] : throw new InvalidOperationException("empty");
    public T? PeekOrDefault() => items.Count > 0 ? items[^1] : default;
}
static class Counter<T> { public static int Count; }
