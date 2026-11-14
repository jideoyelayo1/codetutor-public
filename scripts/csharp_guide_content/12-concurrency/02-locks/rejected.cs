var gate = new object();
lock (gate)
{
    await Task.Yield(); // CS1996: cannot await in the body of a lock statement
}
