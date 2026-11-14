string a = "abc";
string b = new string(new[] { 'a', 'b', 'c' });
Console.WriteLine($"{a == b} {ReferenceEquals(a, b)}");

var t1 = new Ticket(7);
var t2 = new Ticket(7);
Console.WriteLine($"{t1 == t2} {t1.Equals(t2)}");

var s1 = new Seat(3, 'C');
var s2 = new Seat(3, 'C');
Console.WriteLine(s1.Equals(s2));

object boxedA = 5;
object boxedB = 5;
Console.WriteLine($"{boxedA == boxedB} {boxedA.Equals(boxedB)}");
int counter = 1;
object box = counter;      // copies the value into a new heap object
counter++;
Console.WriteLine($"{counter} {box}");
Console.WriteLine((int)box + 1);

class Ticket(int id) { public int Id => id; }
struct Seat(int row, char letter) : IEquatable<Seat>
{
    public int Row => row;
    public char Letter => letter;
    public bool Equals(Seat other) => Row == other.Row && Letter == other.Letter;
    public override bool Equals(object? obj) => obj is Seat other && Equals(other);
    public override int GetHashCode() => HashCode.Combine(Row, Letter);
}
