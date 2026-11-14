Customer[] customers = [new(1, "Ada", "UK"), new(2, "Bob", "US"), new(3, "Cy", "UK"), new(4, "Di", "FR")];
Order[] orders = [new(1, 50m), new(1, 20m), new(2, 99m), new(9, 5m)];
var report = customers
    .LeftJoin(orders, c => c.Id, o => o.CustomerId, (c, o) => (c.Country, Amount: o?.Amount ?? 0m))
    .GroupBy(x => x.Country, x => x.Amount)
    .Select(g => (Country: g.Key, Total: g.Sum()))
    .OrderByDescending(x => x.Total).ThenBy(x => x.Country);
foreach (var (country, total) in report) Console.WriteLine($"{country} {total}");

record Customer(int Id, string Name, string Country);
record Order(int CustomerId, decimal Amount);
