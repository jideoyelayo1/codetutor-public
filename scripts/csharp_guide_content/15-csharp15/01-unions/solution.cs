foreach (var token in Tokenize("x = 42 ;")) Console.WriteLine(Render(token));

static IEnumerable<Token> Tokenize(string text)
{
    foreach (var part in text.Split(' ', StringSplitOptions.RemoveEmptyEntries))
    {
        if (int.TryParse(part, out int n)) yield return n;
        else if (part.Length == 1 && !char.IsLetter(part[0])) yield return part[0];
        else yield return part;
    }
}

static string Render(Token token) => token switch
{
    int n => $"number {n}",
    string name => $"word {name}",
    char symbol => $"symbol {symbol}",
};

public union Token(int, string, char);
