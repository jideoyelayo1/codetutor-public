Counter? c = new Counter();
c?.Value++; // increment and decrement are not allowed with null-conditional access
class Counter { public int Value { get; set; } }
