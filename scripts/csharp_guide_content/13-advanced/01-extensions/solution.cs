var day = new DateOnly(2026, 10, 17);
Console.WriteLine(day.IsWeekend);
Console.WriteLine(DateOnly.Epoch.ToString("yyyy-MM-dd"));

static class DateExtensions
{
    extension(DateOnly date)
    {
        public bool IsWeekend => date.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday;
    }
    extension(DateOnly)
    {
        public static DateOnly Epoch => new(1970, 1, 1);
    }
}
