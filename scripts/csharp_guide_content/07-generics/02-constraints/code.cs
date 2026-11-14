Console.WriteLine(Largest([3, 9, 4]));
Console.WriteLine(Largest(["kiwi", "apple", "fig"]));
var cache = new Pool<StringBuilderLike>();
var item = cache.Rent();
item.Text = "reused";
cache.Return(item);
Console.WriteLine(cache.Rent().Text);
Console.WriteLine(SizeOf<long>() + " " + SizeOf<(byte, byte)>());
Console.WriteLine(FirstName(new Admin("ada")));

static T Largest<T>(IReadOnlyList<T> items) where T : IComparable<T>
{
    if (items.Count == 0) throw new ArgumentException("empty", nameof(items));
    T best = items[0];
    foreach (var x in items) if (x.CompareTo(best) > 0) best = x;
    return best;
}

static unsafe int SizeOf<T>() where T : unmanaged => sizeof(T);
static string FirstName<T>(T user) where T : User => user.Name;

class Pool<T> where T : class, new()
{
    private readonly Stack<T> free = new();
    public T Rent() => free.TryPop(out var item) ? item : new T();
    public void Return(T item) => free.Push(item);
}
class StringBuilderLike { public string Text { get; set; } = ""; }
record User(string Name);
record Admin(string Name) : User(Name);
