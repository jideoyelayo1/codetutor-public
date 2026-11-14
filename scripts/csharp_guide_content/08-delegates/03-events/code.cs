var shop = new Shop();
var audit = new List<string>();
EventHandler<OrderPlaced> log = (sender, e) => audit.Add($"log {e.Id}");
shop.Placed += log;
shop.Placed += (sender, e) => audit.Add($"email {e.Id} for {e.Total}");
shop.Place(1, 20m);
shop.Placed -= log;
shop.Place(2, 35m);
Console.WriteLine(string.Join(" | ", audit));
Console.WriteLine(shop.SubscriberCount);

var noisy = new Shop();
noisy.Placed += (_, _) => throw new InvalidOperationException("handler failed");
noisy.Placed += (_, _) => Console.WriteLine("never reached");
try { noisy.Place(3, 1m); }
catch (InvalidOperationException e) { Console.WriteLine(e.Message); }

record OrderPlaced(int Id, decimal Total);

class Shop
{
    public event EventHandler<OrderPlaced>? Placed;
    public int SubscriberCount => Placed?.GetInvocationList().Length ?? 0;
    public void Place(int id, decimal total) => Placed?.Invoke(this, new OrderPlaced(id, total));
}
