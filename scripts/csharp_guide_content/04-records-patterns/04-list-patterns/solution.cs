foreach (var w in new[] { "level", "abca", "a", "" })
    Console.WriteLine($"{w}: {IsPalindrome(w.ToCharArray())}");

static bool IsPalindrome(char[] cs) => cs switch
{
    [] or [_] => true,
    [var first, .. var middle, var last] => first == last && IsPalindrome(middle),
};
