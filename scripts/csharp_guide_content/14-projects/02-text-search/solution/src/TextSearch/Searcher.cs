namespace TextSearch;

public readonly record struct Match(int LineNumber, string Line);

public static class Searcher
{
    /// <summary>Returns matching lines, numbered from 1, in input order.</summary>
    public static IEnumerable<Match> Search(string query, TextReader input, bool ignoreCase = false)
    {
        ArgumentException.ThrowIfNullOrEmpty(query);
        ArgumentNullException.ThrowIfNull(input);
        var comparison = ignoreCase ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
        return Iterate();

        IEnumerable<Match> Iterate()
        {
            int number = 0;
            while (input.ReadLine() is string line)
            {
                number++;
                if (line.Contains(query, comparison)) yield return new Match(number, line);
            }
        }
    }
}
