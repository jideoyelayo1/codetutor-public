Func<int, int> square = x => x * x;
Func<int, int, int> add = (a, b) => a + b;
Action<string> shout = s => Console.WriteLine(s.ToUpperInvariant());
Console.WriteLine(square(6) + add(1, 2));
shout("delegates");

Validator notEmpty = s => s.Length > 0;
Console.WriteLine(notEmpty("") + " " + notEmpty("x"));

Console.WriteLine(Apply(5, square));
Console.WriteLine(Apply(5, Twice));
var counter = new Counter();
Func<int> next = counter.Next;          // captures the target object
next(); next();
Console.WriteLine(counter.Value);

Action? pipeline = () => Console.Write("a ");
pipeline += () => Console.Write("b ");
pipeline += Done;
pipeline?.Invoke();
pipeline -= Done;            // removal may produce null, hence Action?
pipeline?.Invoke();
Console.WriteLine();

var twice = Twice;                       // natural type: Func<int, int>
Console.WriteLine(new[] { "1", "2" }.Select(int.Parse).Select(twice).Sum());
Action? missing = null;
missing?.Invoke();
Console.WriteLine("null-safe invoke");

static int Apply(int value, Func<int, int> f) => f(value);
static int Twice(int x) => 2 * x;
static void Done() => Console.Write("done ");

delegate bool Validator(string text);
class Counter { public int Value; public int Next() => ++Value; }
