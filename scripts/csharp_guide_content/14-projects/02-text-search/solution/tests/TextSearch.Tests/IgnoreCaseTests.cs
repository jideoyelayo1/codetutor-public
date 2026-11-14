using TextSearch;

namespace TextSearch.Tests;

public class IgnoreCaseTests
{
    [Fact]
    public void MatchesAnyCaseWhenRequested()
    {
        var matches = Searcher.Search("FOX", new StringReader("a fox\nA Fox\nno"), ignoreCase: true);
        Assert.Equal([1, 2], matches.Select(m => m.LineNumber));
    }

    [Fact]
    public void DefaultStaysCaseSensitive() =>
        Assert.Single(Searcher.Search("Fox", new StringReader("a fox\nA Fox")));
}
