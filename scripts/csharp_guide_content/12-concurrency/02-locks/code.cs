var account = new Account();
Parallel.For(0, 1000, _ => account.Deposit(1));
Console.WriteLine(account.Balance);

var a = new BankAccount(1, 100);
var b = new BankAccount(2, 100);
var t1 = Task.Run(() => { for (int i = 0; i < 1000; i++) BankAccount.Transfer(a, b, 1); });
var t2 = Task.Run(() => { for (int i = 0; i < 1000; i++) BankAccount.Transfer(b, a, 1); });
bool finished = Task.WaitAll([t1, t2], TimeSpan.FromSeconds(10));
Console.WriteLine($"no deadlock: {finished}, total preserved: {a.Balance + b.Balance}");

var limiter = new AsyncCounter();
await Task.WhenAll(Enumerable.Range(0, 50).Select(_ => limiter.IncrementAsync()));
Console.WriteLine(limiter.Value);

class Account
{
    private readonly Lock gate = new();
    private decimal balance;
    public void Deposit(decimal amount) { lock (gate) balance += amount; }
    public decimal Balance { get { lock (gate) return balance; } }
}

class BankAccount(int id, decimal opening)
{
    private readonly Lock gate = new();
    public int Id => id;
    public decimal Balance { get; private set; } = opening;

    public static void Transfer(BankAccount from, BankAccount to, decimal amount)
    {
        var (first, second) = from.Id < to.Id ? (from, to) : (to, from);   // global lock order
        lock (first.gate)
        lock (second.gate)
        {
            from.Balance -= amount;
            to.Balance += amount;
        }
    }
}

class AsyncCounter
{
    private readonly SemaphoreSlim gate = new(1, 1);
    public int Value { get; private set; }
    public async Task IncrementAsync()
    {
        await gate.WaitAsync();
        try
        {
            int read = Value;
            await Task.Yield();       // awaiting while holding the semaphore is allowed
            Value = read + 1;
        }
        finally { gate.Release(); }
    }
}
