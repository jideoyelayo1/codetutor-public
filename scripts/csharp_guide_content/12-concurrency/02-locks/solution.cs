var log = new BoundedLog(3);
Parallel.For(0, 10, i => log.Add($"m{i}"));
Console.WriteLine(log.Snapshot().Length);

class BoundedLog(int capacity)
{
    private readonly Lock gate = new();
    private readonly Queue<string> messages = new();
    public void Add(string message)
    {
        lock (gate)
        {
            messages.Enqueue(message);
            if (messages.Count > capacity) messages.Dequeue();
        }
    }
    public string[] Snapshot() { lock (gate) return messages.ToArray(); }
}
