var graph = new Dictionary<char, char[]>
{
    ['a'] = ['b', 'c'], ['b'] = ['d'], ['c'] = ['d', 'e'], ['d'] = [], ['e'] = [],
};
var visited = new HashSet<char> { 'a' };
var frontier = new Queue<char>(['a']);
while (frontier.TryDequeue(out var node))
{
    Console.Write(node);
    foreach (var next in graph[node])
        if (visited.Add(next)) frontier.Enqueue(next);
}
Console.WriteLine();
