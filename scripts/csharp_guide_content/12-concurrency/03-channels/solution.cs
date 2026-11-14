using System.Threading.Channels;

var numbers = Channel.CreateBounded<int>(1);
var squares = Channel.CreateBounded<int>(1);
var source = Task.Run(async () =>
{
    for (int i = 1; i <= 5; i++) await numbers.Writer.WriteAsync(i);
    numbers.Writer.Complete();
});
var square = Task.Run(async () =>
{
    await foreach (var n in numbers.Reader.ReadAllAsync()) await squares.Writer.WriteAsync(n * n);
    squares.Writer.Complete();
});
await foreach (var s in squares.Reader.ReadAllAsync()) Console.Write(s + " ");
Console.WriteLine();
await Task.WhenAll(source, square);
