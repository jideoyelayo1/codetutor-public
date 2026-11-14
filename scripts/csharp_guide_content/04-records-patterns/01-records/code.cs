var ada = new Person("Ada", 36);
var twin = new Person("Ada", 36);
Console.WriteLine(ada);
Console.WriteLine($"{ada == twin} {ReferenceEquals(ada, twin)}");
var older = ada with { Age = 37 };
Console.WriteLine($"{ada.Age} {older.Age}");
var (name, age) = older;
Console.WriteLine($"{name} is {age}");

var p1 = new Point(1, 2);
var p2 = p1 with { Y = 5 };
Console.WriteLine($"{p1} {p2}");

var a = new Team("red", ["x"]);
var b = new Team("red", ["x"]);
Console.WriteLine(a == b);   // List compared by reference

record Person(string Name, int Age);
readonly record struct Point(int X, int Y);
record Team(string Color, List<string> Members);
