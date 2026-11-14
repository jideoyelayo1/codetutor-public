using System.Collections.Immutable;

var stock = ImmutableDictionary<string, int>.Empty
    .Add("apples", 5).Add("pears", 2).Add("plums", 0);
var restocked = stock.SetItem("plums", 12);
Console.WriteLine($"{stock["plums"]} {restocked["plums"]}");
