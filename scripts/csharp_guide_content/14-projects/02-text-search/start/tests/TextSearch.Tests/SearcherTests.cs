using TextSearch;

namespace TextSearch.Tests;

public class SearcherTests
{
    private const string Poem = "The quick fox\nlazy dog\nA fox again\nfoxglove";

    [Fact]
    public void FindsMatchingLinesWithNumbers()
    {
        var matches = Searcher.Search("fox", new StringReader(Poem)).ToList();
        Assert.Equal([new Match(1, "The quick fox"), new Match(3, "A fox again"), new Match(4, "foxglove")], matches);
    }

    [Fact]
    public void IsCaseSensitive() => Assert.Empty(Searcher.Search("FOX", new StringReader(Poem)));

    [Fact]
    public void RejectsEmptyQueryImmediately() =>
        Assert.Throws<ArgumentException>(() => Searcher.Search("", new StringReader(Poem)));

    [Fact]
    public void ReadsLazily()
    {
        var reader = new CountingReader("fox\nfox\nfox");
        var first = Searcher.Search("fox", reader).First();
        Assert.Equal(1, first.LineNumber);
        Assert.Equal(1, reader.LinesRead);
    }

    private sealed class CountingReader(string text) : StringReader(text)
    {
        public int LinesRead { get; private set; }
        public override string? ReadLine()
        {
            var line = base.ReadLine();
            if (line is not null) LinesRead++;
            return line;
        }
    }
}
