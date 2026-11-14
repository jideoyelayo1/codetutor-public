using System.Linq.Expressions;

var s = Expression.Parameter(typeof(string), "s");
var test = Expression.Lambda<Func<string, bool>>(
    Expression.GreaterThan(Expression.Property(s, nameof(string.Length)), Expression.Constant(3)), s);
Console.WriteLine(test);
var keep = test.Compile();
Console.WriteLine(string.Join(",", new[] { "to", "tree", "leaf" }.Where(keep)));
