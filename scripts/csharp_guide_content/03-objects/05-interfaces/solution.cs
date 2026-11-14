List<Version> versions = [new(1, 4), new(0, 9), new(1, 10)];
versions.Sort();
Console.WriteLine(string.Join(" ", versions));

sealed class Version(int major, int minor) : IComparable<Version>
{
    public int Major => major;
    public int Minor => minor;
    public int CompareTo(Version? other)
    {
        if (other is null) return 1;
        int byMajor = Major.CompareTo(other.Major);
        return byMajor != 0 ? byMajor : Minor.CompareTo(other.Minor);
    }
    public override string ToString() => $"{Major}.{Minor}";
}
