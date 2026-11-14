var p1 = new PointStruct { X = 1 };
var p2 = p1;          // copies the whole struct
p2.X = 99;
Console.WriteLine($"struct: p1.X={p1.X} p2.X={p2.X}");

var c1 = new PointClass { X = 1 };
var c2 = c1;          // copies the reference only
c2.X = 99;
Console.WriteLine($"class: c1.X={c1.X} c2.X={c2.X} same={ReferenceEquals(c1, c2)}");

Mutate(c1);
Console.WriteLine($"after Mutate: {c1.X}");
Replace(c1);
Console.WriteLine($"after Replace: {c1.X}");
ReplaceRef(ref c1);
Console.WriteLine($"after ReplaceRef: {c1.X}");

static void Mutate(PointClass p) => p.X = 7;
static void Replace(PointClass p) => p = new PointClass { X = -1 };
static void ReplaceRef(ref PointClass p) => p = new PointClass { X = -1 };

struct PointStruct { public int X; }
class PointClass { public int X; }
