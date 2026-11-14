int[] values = [3, 8, 1, 9, 4];
Console.WriteLine(string.Join(",", values[^2..]));
int first = values[0];
Array.Copy(values, 1, values, 0, values.Length - 1);
values[^1] = first;
Console.WriteLine(string.Join(",", values));
