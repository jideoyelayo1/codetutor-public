Console.WriteLine(Bad());
static ref int Bad()
{
    int local = 1;
    return ref local; // CS8168: cannot return a local by reference
}
