Status s = Status.Active;
Console.WriteLine($"{s} = {(int)s}");
Console.WriteLine(Enum.TryParse("closed", ignoreCase: true, out Status parsed) ? parsed : Status.Pending);
Status odd = (Status)42;
Console.WriteLine($"{odd} defined={Enum.IsDefined(odd)}");
Console.WriteLine(string.Join(",", Enum.GetValues<Status>()));

Permissions p = Permissions.Read | Permissions.Write;
Console.WriteLine(p);
Console.WriteLine(p.HasFlag(Permissions.Write));
p &= ~Permissions.Write;
Console.WriteLine(p);
Console.WriteLine(Label(Status.Closed));

static string Label(Status status) => status switch
{
    Status.Pending => "waiting",
    Status.Active => "running",
    Status.Closed => "done",
    _ => "unknown",
};

enum Status { Pending, Active, Closed }

[Flags]
enum Permissions { None = 0, Read = 1, Write = 2, Execute = 4 }
