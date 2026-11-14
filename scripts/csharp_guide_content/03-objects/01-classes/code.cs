var a = new Account("Ada");
var b = new Account("Bob", 100m) { Nickname = "B" };
a.Deposit(25m);
Console.WriteLine(a);
Console.WriteLine(b);
Console.WriteLine($"accounts created: {Account.Count}");

class Account
{
    public static int Count { get; private set; }
    private readonly string owner;
    private decimal balance;
    public string? Nickname { get; set; }

    public Account(string owner) : this(owner, 0m) { }
    public Account(string owner, decimal opening)
    {
        this.owner = owner;
        balance = opening;
        Count++;
    }

    public void Deposit(decimal amount) => balance += amount;
    public override string ToString() => $"{owner}{(Nickname is null ? "" : $" ({Nickname})")}: {balance}";
}
