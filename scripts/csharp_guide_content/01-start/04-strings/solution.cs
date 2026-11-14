using System.Text;

var builder = new StringBuilder();
for (int i = 0; i < 5; i++)
{
    if (i > 0) builder.Append(',');
    builder.Append(i);
}
string result = builder.ToString();
Console.WriteLine(result);
Console.WriteLine(result.Length);
