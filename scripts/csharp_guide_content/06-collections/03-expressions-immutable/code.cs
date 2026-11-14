using System.Collections.Frozen;
using System.Collections.Immutable;

int[] middle = [2, 3];
List<int> list = [1, .. middle, 4];
int[] empty = [];
Console.WriteLine($"{string.Join(",", list)} {empty.Length}");

ImmutableList<string> v1 = ["a", "b"];
ImmutableList<string> v2 = v1.Add("c");
Console.WriteLine($"{v1.Count} {v2.Count}");

var builder = ImmutableArray.CreateBuilder<int>();
for (int i = 0; i < 3; i++) builder.Add(i * i);
ImmutableArray<int> squares = builder.ToImmutable();
Console.WriteLine(string.Join(",", squares));

FrozenDictionary<string, int> ports = new Dictionary<string, int> { ["http"] = 80, ["https"] = 443 }.ToFrozenDictionary();
Console.WriteLine(ports["https"]);
FrozenSet<string> admins = new[] { "ada", "bob" }.ToFrozenSet();
Console.WriteLine(admins.Contains("ada"));

var source = new List<int> { 1 };
IReadOnlyList<int> view = source;
source.Add(2);
Console.WriteLine(view.Count);
