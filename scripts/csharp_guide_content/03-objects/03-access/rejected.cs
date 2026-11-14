var a = new Account();
a.Balance = 10; // CS0272: the set accessor is inaccessible
class Account { public decimal Balance { get; private set; } }
