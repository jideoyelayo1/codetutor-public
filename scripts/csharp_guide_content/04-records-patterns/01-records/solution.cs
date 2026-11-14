var order = new Order(1, 99.5m, "new");
var shipped = order with { Status = "shipped" };
Console.WriteLine(order);
Console.WriteLine(shipped);
Console.WriteLine(order == shipped);

record Order(int Id, decimal Total, string Status);
