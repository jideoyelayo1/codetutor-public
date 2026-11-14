string[] values = ["one", "two", "three"];
List<string> names = [with(capacity: values.Length * 2), .. values];
Console.WriteLine($"{names.Count} items, capacity {names.Capacity}");

HashSet<string> set = [with(StringComparer.OrdinalIgnoreCase), "Hello", "HELLO", "hello"];
Console.WriteLine(set.Count);

Dictionary<string, int> ages = [with(StringComparer.OrdinalIgnoreCase)];
ages["Ada"] = 36;
Console.WriteLine(ages["ADA"]);

IEnumerable<int> numbers = Enumerable.Range(1, 10);
Console.WriteLine(numbers[2]);
var queue = new Queue<string>(["first", "second", "third"]);
Console.WriteLine(queue[1]);

static class SequenceIndexer
{
    extension(IEnumerable<int> sequence)
    {
        public int this[int index] => sequence.ElementAt(index);
    }
    extension<T>(Queue<T> queue)       // Queue<T> has no indexer of its own
    {
        public T this[int index] => queue.ElementAt(index);
    }
}
