Customer? none = null;
Customer? some = new();
int calls = 0;
string NextOrder() { calls++; return $"order-{calls}"; }

none?.Order = NextOrder();         // right side not evaluated
some?.Order = NextOrder();
Console.WriteLine($"{some?.Order} after {calls} call(s)");
var target = new Customer();
target.Counter?.Value += 5;        // Counter is null: nothing happens
target.Counter = new Counter();
target.Counter?.Value += 5;
Console.WriteLine(target.Counter?.Value);

Console.WriteLine(nameof(List<>) + " " + nameof(Dictionary<,>));

var sensor = new Sensor("probe");
sensor.Changed += (_, v) => Console.WriteLine($"changed to {v}");
sensor.Set(3);
Console.WriteLine(sensor.Name);

class Customer
{
    public string? Order { get; set; }
    public Counter? Counter { get; set; }
}
class Counter { public int Value { get; set; } }

// Defining declarations, as a generator's input might look.
partial class Sensor
{
    public partial Sensor(string name);
    public partial event EventHandler<int>? Changed;
}

// Implementing declarations.
partial class Sensor
{
    private EventHandler<int>? changed;
    public string Name { get; }
    public partial Sensor(string name) : this() => Name = name.ToUpperInvariant();
    private Sensor() => Name = "";
    public partial event EventHandler<int>? Changed
    {
        add => changed += value;
        remove => changed -= value;
    }
    public void Set(int value) => changed?.Invoke(this, value);
}
