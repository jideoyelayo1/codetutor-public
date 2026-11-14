using System.Buffers;

Console.WriteLine(ReverseWords("one two three"));

static string ReverseWords(string text)
{
    string[] words = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    char[] buffer = ArrayPool<char>.Shared.Rent(text.Length);
    try
    {
        int length = 0;
        for (int i = words.Length - 1; i >= 0; i--)
        {
            if (length > 0) buffer[length++] = ' ';
            words[i].CopyTo(buffer.AsSpan(length));
            length += words[i].Length;
        }
        return new string(buffer, 0, length);
    }
    finally
    {
        ArrayPool<char>.Shared.Return(buffer);
    }
}
