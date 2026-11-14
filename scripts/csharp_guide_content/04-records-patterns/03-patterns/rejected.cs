Console.WriteLine(Grade(5));
static string Grade(int score) => score switch
{
    >= 0 => "any",
    >= 90 => "A",   // CS8510: subsumed by the previous arm
    _ => "negative",
};
