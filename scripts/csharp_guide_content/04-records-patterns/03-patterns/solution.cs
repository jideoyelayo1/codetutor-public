foreach (var t in new[] { (6, false), (10, true), (10, false), (20, true) })
    Console.WriteLine(Plan(t));

static string Plan((int Hour, bool Weekend) t) => t switch
{
    ( < 7, _) => "sleep",
    (>= 7 and <= 11, true) => "brunch",
    (>= 9 and <= 16, false) => "work",
    _ => "free",
};
