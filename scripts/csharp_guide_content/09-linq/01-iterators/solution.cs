Console.WriteLine(string.Join(" ", Primes().Take(10)));

static IEnumerable<int> Primes()
{
    var found = new List<int>();
    for (int candidate = 2; ; candidate++)
    {
        bool prime = true;
        foreach (var p in found)
        {
            if (p * p > candidate) break;
            if (candidate % p == 0) { prime = false; break; }
        }
        if (prime) { found.Add(candidate); yield return candidate; }
    }
}
