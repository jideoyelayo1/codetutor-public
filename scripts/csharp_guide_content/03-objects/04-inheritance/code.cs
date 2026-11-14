List<Shape> shapes = [new Circle(1), new Square(2), new Square(1) { Label = "tile" }];
foreach (Shape s in shapes)
    Console.WriteLine($"{s.Describe()} area={s.Area():F2}");

Base hidden = new Derived();
Console.WriteLine(hidden.Name());            // hiding: chosen by static type
Console.WriteLine(((Derived)hidden).Name());

abstract class Shape
{
    public string Label { get; init; } = "shape";
    public abstract double Area();
    public virtual string Describe() => Label;
}

sealed class Circle(double radius) : Shape
{
    public override double Area() => Math.PI * radius * radius;
    public override string Describe() => "circle " + base.Describe();
}

class Square(double side) : Shape
{
    public override double Area() => side * side;
}

class Base { public string Name() => "base"; }
class Derived : Base { public new string Name() => "derived"; }
