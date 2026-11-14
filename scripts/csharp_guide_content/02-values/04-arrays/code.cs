int[] scores = new int[3];
scores[1] = 80;
Console.WriteLine(string.Join(",", scores));
int[] primes = [2, 3, 5, 7, 11];
Console.WriteLine($"{primes[0]} {primes[^1]} {primes.Length}");
int[] middle = primes[1..4];
middle[0] = 99;   // a range on an array is a copy
Console.WriteLine($"{string.Join(",", middle)} | {string.Join(",", primes)}");

int[,] grid = new int[2, 3];
for (int r = 0; r < grid.GetLength(0); r++)
    for (int c = 0; c < grid.GetLength(1); c++)
        grid[r, c] = r * 10 + c;
Console.WriteLine(grid[1, 2]);

int[][] jagged = [[1], [2, 3], [4, 5, 6]];
foreach (int[] row in jagged) Console.Write(row.Length + " ");
Console.WriteLine();

int[] data = [5, 1, 4];
int[] alias = data;
Array.Sort(data);
Console.WriteLine(string.Join(",", alias));
try { Console.WriteLine(data[3]); }
catch (IndexOutOfRangeException) { Console.WriteLine("index 3 is out of range"); }
