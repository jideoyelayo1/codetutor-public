int factor = 3;
Func<int, int> scale = static x => x * factor; // CS8820: a static anonymous function cannot capture 'factor'
Console.WriteLine(scale(2));
