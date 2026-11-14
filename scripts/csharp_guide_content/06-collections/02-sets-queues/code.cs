var seen = new HashSet<int>();
foreach (var n in new[] { 3, 1, 3, 2, 1 })
    Console.Write(seen.Add(n) ? $"+{n} " : $"dup{n} ");
Console.WriteLine();
var evens = new HashSet<int> { 2, 4 };
seen.IntersectWith(evens);
Console.WriteLine(string.Join(",", seen));

var queue = new Queue<string>(["first", "second"]);
queue.Enqueue("third");
Console.WriteLine(queue.Dequeue() + " then " + queue.Peek());

var undo = new Stack<string>();
undo.Push("type a"); undo.Push("type b");
Console.WriteLine(undo.Pop());
Console.WriteLine(undo.TryPop(out var next) ? next : "empty");
Console.WriteLine(undo.TryPop(out _) ? "more" : "empty");

var tasks = new PriorityQueue<string, (int Priority, int Order)>();
int order = 0;
foreach (var (name, priority) in new[] { ("email", 3), ("outage", 1), ("lunch", 3), ("deploy", 2) })
    tasks.Enqueue(name, (priority, order++));
while (tasks.TryDequeue(out var task, out var p)) Console.Write($"{task}({p.Priority}) ");
Console.WriteLine();
