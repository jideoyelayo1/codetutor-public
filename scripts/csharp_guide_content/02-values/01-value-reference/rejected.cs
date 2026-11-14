var points = new List<P> { new P() };
points[0].X = 5; // CS1612: cannot modify the return value because it is not a variable
struct P { public int X; }
