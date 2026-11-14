var two = new Node { Next = new Node() };
var one = new Node();
two.Next?.Visits += 1;
one.Next?.Visits += 1;
Console.WriteLine(two.Next?.Visits);
Console.WriteLine(one.Next?.Visits is null);

class Node
{
    public Node? Next { get; set; }
    public int Visits { get; set; }
}
