var cart = new Cart();
cart.Add("apple");
cart.Add("pear");
IReadOnlyList<string> view = cart.Items;
Console.WriteLine(view.Count);
cart.Add("plum");
Console.WriteLine(view.Count);              // a view, not a snapshot
Console.WriteLine(view is List<string>);    // callers could still cast back...
Console.WriteLine(cart.Snapshot().Length);  // ...so return a copy when that matters

var account = new BankAccount(100);
Console.WriteLine(account.TryWithdraw(30) + " " + account.Balance);
Console.WriteLine(account.TryWithdraw(500) + " " + account.Balance);
Console.WriteLine(Limits.MaxItems);

class Cart
{
    private readonly List<string> items = [];
    public IReadOnlyList<string> Items => items;
    public void Add(string item) => items.Add(item);
    public string[] Snapshot() => items.ToArray();
}

class BankAccount(decimal opening)
{
    public decimal Balance { get; private set; } = opening;
    public bool TryWithdraw(decimal amount)
    {
        if (amount <= 0 || amount > Balance) return false;
        Balance -= amount;
        return true;
    }
}

static class Limits
{
    public static readonly int MaxItems = 10;
}
