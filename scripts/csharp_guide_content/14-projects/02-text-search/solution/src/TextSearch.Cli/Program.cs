using TextSearch;

bool ignoreCase = args is ["-i", ..] or ["--ignore-case", ..];
string[] rest = ignoreCase ? args[1..] : args;
if (rest is not [var query, var path])
{
    Console.Error.WriteLine("usage: textsearch [-i|--ignore-case] <query> <file>");
    return 1;
}
if (!File.Exists(path))
{
    Console.Error.WriteLine($"file not found: {path}");
    return 2;
}
using var reader = File.OpenText(path);
foreach (var match in Searcher.Search(query, reader, ignoreCase))
    Console.WriteLine($"{match.LineNumber}: {match.Line}");
return 0;
