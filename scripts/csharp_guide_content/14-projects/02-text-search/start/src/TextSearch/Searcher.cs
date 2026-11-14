namespace TextSearch;

public readonly record struct Match(int LineNumber, string Line);

public static class Searcher
{
    /// <summary>Returns matching lines, numbered from 1, in input order.</summary>
    public static IEnumerable<Match> Search(string query, TextReader input)
    {
        ArgumentException.ThrowIfNullOrEmpty(query);
        ArgumentNullException.ThrowIfNull(input);
        return Iterate();

        IEnumerable<Match> Iterate()
        {
            int number = 0;
            while (input.ReadLine() is string line)
            {
                number++;
                if (line.Contains(query, StringComparison.Ordinal)) yield return new Match(number, line);
            }
        }
    }
}
