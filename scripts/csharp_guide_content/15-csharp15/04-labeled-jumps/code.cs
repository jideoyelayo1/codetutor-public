int[][] grid = [[1, 2, 3], [4, -1, 6], [7, 8, 9]];
var visited = new List<int>();
outer: for (int r = 0; r < grid.Length; r++)
{
    for (int c = 0; c < grid[r].Length; c++)
    {
        if (grid[r][c] < 0) continue outer;    // skip the rest of this row
        if (grid[r][c] == 8) break outer;      // stop the whole search
        visited.Add(grid[r][c]);
    }
}
Console.WriteLine(string.Join(",", visited));

var pairs = new List<string>();
search: foreach (var a in new[] { 1, 2, 3, 4 })
    foreach (var b in new[] { 5, 6, 7 })
        if (a * b == 12)
        {
            pairs.Add($"{a}x{b}");
            break search;
        }
Console.WriteLine(string.Join(",", pairs));
