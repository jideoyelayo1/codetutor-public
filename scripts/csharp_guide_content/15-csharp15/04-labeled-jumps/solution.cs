string[] lines = ["1,2,3", "4,x,5", "6"];
var sums = new List<int>();
lines: foreach (var line in lines)
{
    int sum = 0;
    foreach (var part in line.Split(','))
    {
        if (!int.TryParse(part, out int n)) continue lines;
        sum += n;
    }
    sums.Add(sum);
}
Console.WriteLine(string.Join(",", sums));
