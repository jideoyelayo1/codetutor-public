var t1 = new Ticket(7);
var t2 = new Ticket(7);
Console.WriteLine($"{t1 == t2} {t1.Equals(t2)} {ReferenceEquals(t1, t2)}");
var set = new HashSet<Ticket> { t1, t2 };
Console.WriteLine(set.Count);

class Ticket(int id) : IEquatable<Ticket>
{
    public int Id => id;
    public bool Equals(Ticket? other) => other is not null && Id == other.Id;
    public override bool Equals(object? obj) => Equals(obj as Ticket);
    public override int GetHashCode() => Id.GetHashCode();
    public static bool operator ==(Ticket? left, Ticket? right) => left is null ? right is null : left.Equals(right);
    public static bool operator !=(Ticket? left, Ticket? right) => !(left == right);
}
