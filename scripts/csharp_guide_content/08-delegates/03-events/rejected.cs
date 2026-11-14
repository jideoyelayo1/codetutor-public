var s = new Shop();
s.Placed?.Invoke(s, 1); // CS0070: the event can only appear on the left of += or -= outside Shop
class Shop { public event EventHandler<int>? Placed; }
