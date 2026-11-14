List<Employee> staff = [new Salaried(60000m), new Hourly(20m, 160)];
foreach (var e in staff) Console.WriteLine($"{e.Title}: {e.MonthlyPay()}");
Console.WriteLine(staff.Sum(e => e.MonthlyPay()));

abstract class Employee
{
    public virtual string Title => "employee";
    public abstract decimal MonthlyPay();
}
sealed class Salaried(decimal annual) : Employee
{
    public override string Title => "salaried";
    public override decimal MonthlyPay() => annual / 12;
}
sealed class Hourly(decimal rate, int hours) : Employee
{
    public override decimal MonthlyPay() => rate * hours;
}
