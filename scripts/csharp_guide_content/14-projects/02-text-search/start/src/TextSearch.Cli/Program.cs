using TextSearch;

if (args is not [var query, var path])
{
    Console.Error.WriteLine("usage: textsearch <query> <file>");
    return 1;
}
if (!File.Exists(path))
{
    Console.Error.WriteLine($"file not found: {path}");
    return 2;
}
using var reader = File.OpenText(path);
foreach (var match in Searcher.Search(query, reader))
    Console.WriteLine($"{match.LineNumber}: {match.Line}");
return 0;
