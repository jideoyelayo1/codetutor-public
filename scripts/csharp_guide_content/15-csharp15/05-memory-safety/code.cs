int number = 41;
int* pointer = &number;                 // no unsafe context needed in preview
Console.WriteLine(unsafe(*pointer) + 1);  // dereferencing still requires unsafe
Console.WriteLine(sizeof(long));

int[] numbers = [10, 20, 30];
fixed (int* first = numbers)
{
    unsafe { Console.WriteLine(first[2]); }
}
Console.WriteLine(Header.Signature);

class Header
{
    // A field initializer cannot hold an unsafe block, but can use an unsafe expression.
    public static readonly int Signature = unsafe(ReadSignature());
    static unsafe int ReadSignature()
    {
        int raw = 0x1234;
        int* p = &raw;
        return *p;
    }
}
