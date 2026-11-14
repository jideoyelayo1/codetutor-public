Func<int, int> addOne = x => x + 1;
Func<int, int> twice = x => x * 2;
Console.WriteLine(Compose(addOne, twice)(3));
Console.WriteLine(Compose(twice, addOne)(3));

static Func<int, int> Compose(Func<int, int> f, Func<int, int> g) => x => g(f(x));
