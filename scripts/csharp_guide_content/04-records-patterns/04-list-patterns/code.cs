int[][] samples = [[], [7], [1, 2], [5, 0, 0, -1], [1, 2, 3]];
foreach (var s in samples) Console.WriteLine(Describe(s));
Console.WriteLine(Sum([1, 2, 3, 4]));
Console.WriteLine(Run(["add", "2", "3"]));
Console.WriteLine(Run(["neg", "8"]));
Console.WriteLine(Run(["oops"]));

static string Describe(int[] xs) => xs switch
{
    [] => "empty",
    [var only] => $"one: {only}",
    [1, 2, 3] => "exactly 1,2,3",
    [> 0, .., < 0] => "starts positive, ends negative",
    [var first, .. var middle, var last] => $"{first}..{last} with {middle.Length} between",
};

static int Sum(int[] xs) => xs switch
{
    [] => 0,
    [var head, .. var tail] => head + Sum(tail),
};

static string Run(string[] command) => command switch
{
    ["add", var a, var b] => (int.Parse(a) + int.Parse(b)).ToString(),
    ["neg", var a] => (-int.Parse(a)).ToString(),
    [var name, ..] => $"unknown command {name}",
    [] => "no command",
};
