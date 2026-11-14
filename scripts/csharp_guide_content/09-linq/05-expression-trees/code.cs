using System.Linq.Expressions;

Func<int, bool> asCode = x => x > 2;
Expression<Func<int, bool>> asData = x => x > 2;
Console.WriteLine(asCode(5));
Console.WriteLine(asData);
var body = (BinaryExpression)asData.Body;
Console.WriteLine($"{body.NodeType} {body.Left} {body.Right}");
Console.WriteLine(asData.Compile()(1));

var parameter = Expression.Parameter(typeof(int), "n");
var built = Expression.Lambda<Func<int, int>>(Expression.Multiply(parameter, Expression.Constant(3)), parameter);
Console.WriteLine($"{built} -> {built.Compile()(7)}");

IQueryable<int> query = new[] { 1, 2, 3, 4 }.AsQueryable().Where(n => n % 2 == 0).Select(n => n * 10);
Console.WriteLine(query.Expression.ToString().Contains("Where"));
Console.WriteLine(string.Join(",", query));
