struct Holder
{
    private int value;
    public ref int Value => ref value; // CS8170: a struct cannot return its own field by reference
}
