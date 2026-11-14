Days weekend = Days.Weekend;
Console.WriteLine(weekend.HasFlag(Days.Sunday));
Console.WriteLine(weekend);
Console.WriteLine(Days.Saturday | Days.Sunday);

[Flags]
enum Days
{
    None = 0, Monday = 1, Tuesday = 2, Wednesday = 4, Thursday = 8, Friday = 16, Saturday = 32, Sunday = 64,
    Weekend = Saturday | Sunday,
}
