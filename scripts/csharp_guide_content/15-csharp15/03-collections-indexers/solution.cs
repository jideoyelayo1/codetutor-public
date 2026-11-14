SortedSet<string> fruit = [with(Comparer<string>.Create((a, b) => string.CompareOrdinal(b, a))), "apple", "cherry", "banana"];
Console.WriteLine(string.Join(",", fruit));
