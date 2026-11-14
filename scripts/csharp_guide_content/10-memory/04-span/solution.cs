Console.WriteLine(CountWords("  the quick  brown fox "));

static int CountWords(ReadOnlySpan<char> text)
{
    int count = 0;
    while (true)
    {
        text = text.TrimStart(' ');
        if (text.IsEmpty) return count;
        count++;
        int space = text.IndexOf(' ');
        if (space < 0) return count;
        text = text[space..];
    }
}
