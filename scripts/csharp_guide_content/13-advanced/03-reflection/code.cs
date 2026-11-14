using System.Reflection;
using System.Runtime.CompilerServices;

foreach (var property in typeof(Signup).GetProperties())
{
    var rule = property.GetCustomAttribute<MaxLengthAttribute>();
    Console.WriteLine($"{property.Name}: {property.PropertyType.Name}{(rule is null ? "" : $" max {rule.Length}")}");
}

var form = new Signup { Name = "Ada Lovelace", Email = "ada@example.com" };
Console.WriteLine(string.Join("; ", Validate(form)));
Console.WriteLine(string.Join("; ", Validate(form with { Name = "A very long name indeed" })));

var method = typeof(Math).GetMethod(nameof(Math.Max), [typeof(int), typeof(int)])!;
Console.WriteLine(method.Invoke(null, [3, 9]));
Console.WriteLine(typeof(Signup).GetCustomAttribute<ObsoleteAttribute>()?.Message);
Log();
Check(form.Name.Length > 100);

static IEnumerable<string> Validate(object target)
{
    var problems = new List<string>();
    foreach (var p in target.GetType().GetProperties())
        if (p.GetCustomAttribute<MaxLengthAttribute>() is { } rule && p.GetValue(target) is string s && s.Length > rule.Length)
            problems.Add($"{p.Name} exceeds {rule.Length}");
    return problems.Count == 0 ? ["valid"] : problems;
}

static void Log([CallerMemberName] string caller = "") => Console.WriteLine($"called from {caller}");
static void Check(bool condition, [CallerArgumentExpression(nameof(condition))] string text = "") =>
    Console.WriteLine($"{text} is {condition}");

[AttributeUsage(AttributeTargets.Property)]
sealed class MaxLengthAttribute(int length) : Attribute
{
    public int Length => length;
}

[Obsolete("Use SignupV2")]
record Signup
{
    [MaxLength(20)] public string Name { get; init; } = "";
    public string Email { get; init; } = "";
}
