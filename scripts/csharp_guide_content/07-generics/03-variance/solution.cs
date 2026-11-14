ISource<string> words = new Words();
ISource<object> objects = words;     // allowed: out T and string is a reference type
Console.WriteLine(objects.Next());
Console.WriteLine(words is ISource<object>);
Console.WriteLine(new Numbers() is ISource<object>);   // variance never applies to value types

interface ISource<out T> { T Next(); }
class Words : ISource<string> { public string Next() => "word"; }
class Numbers : ISource<int> { public int Next() => 1; }
