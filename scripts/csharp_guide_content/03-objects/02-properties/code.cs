var user = new User { Email = "  Ada@Example.COM ", Name = "Ada" };
Console.WriteLine(user.Email);
user.Name = "Ada L.";
Console.WriteLine(user.Name);
try { user.Name = ""; }
catch (ArgumentException e) { Console.WriteLine(e.Message); }
Console.WriteLine(user.Id);
Console.WriteLine(user.Visits);
user.Visit(); user.Visit();
Console.WriteLine(user.Visits);

class User
{
    private static int next = 1;
    public int Id { get; } = next++;
    public required string Name
    {
        get;
        set => field = string.IsNullOrWhiteSpace(value) ? throw new ArgumentException("Name is required") : value;
    }
    public required string Email
    {
        get;
        init => field = value.Trim().ToLowerInvariant();
    }
    public int Visits { get; private set; }
    public void Visit() => Visits++;
}
