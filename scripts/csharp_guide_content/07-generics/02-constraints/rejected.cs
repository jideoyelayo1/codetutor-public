Console.WriteLine(Largest(new object(), new object())); // CS0311: object does not satisfy IComparable<object>
static T Largest<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b) >= 0 ? a : b;
