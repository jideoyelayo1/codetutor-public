Customer[] customers = [new(1, "Ada", "UK"), new(2, "Bob", "US"), new(3, "Cy", "UK"), new(4, "Di", "FR")];
Order[] orders = [new(1, 50m), new(1, 20m), new(2, 99m), new(9, 5m)];

var ukNames = customers.Where(c => c.Country == "UK").Select(c => c.Name);
Console.WriteLine(string.Join(",", ukNames));

foreach (var g in customers.GroupBy(c => c.Country).OrderBy(g => g.Key))
    Console.Write($"{g.Key}:{g.Count()} ");
Console.WriteLine();

var totals = from c in customers
             join o in orders on c.Id equals o.CustomerId
             group o.Amount by c.Name into g
             orderby g.Key
             select $"{g.Key}={g.Sum()}";
Console.WriteLine(string.Join(" ", totals));

var everyone = customers.LeftJoin(orders, c => c.Id, o => o.CustomerId,
    (c, o) => $"{c.Name}:{o?.Amount.ToString() ?? "none"}");
Console.WriteLine(string.Join(" ", everyone));

var byCountry = customers.ToLookup(c => c.Country);
Console.WriteLine(string.Join(",", byCountry["UK"].Select(c => c.Name)));
Console.WriteLine(byCountry["JP"].Any());

var sorted = customers.OrderByDescending(c => c.Country).ThenBy(c => c.Name).Select(c => c.Name);
Console.WriteLine(string.Join(",", sorted));
var pairs = new[] { new[] { 1, 2 }, new[] { 3 } }.SelectMany(xs => xs);
Console.WriteLine(pairs.Sum());

record Customer(int Id, string Name, string Country);
record Order(int CustomerId, decimal Amount);
