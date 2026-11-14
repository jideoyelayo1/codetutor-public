using System.Runtime.CompilerServices;

var clock = new Clock();
WeakReference leaked = OpenWindow(clock, unsubscribe: false);
WeakReference released = OpenWindow(clock, unsubscribe: true);
GC.Collect();
GC.WaitForPendingFinalizers();
GC.Collect();
Console.WriteLine($"subscribed window alive: {leaked.IsAlive}");
Console.WriteLine($"unsubscribed window alive: {released.IsAlive}");
Console.WriteLine($"clock subscribers: {clock.SubscriberCount}");
clock.Tick();

[MethodImpl(MethodImplOptions.NoInlining)]
static WeakReference OpenWindow(Clock clock, bool unsubscribe)
{
    var window = new Window(clock);
    if (unsubscribe) window.Close();
    return new WeakReference(window);
}

class Clock
{
    public event EventHandler? Ticked;
    public int SubscriberCount => Ticked?.GetInvocationList().Length ?? 0;
    public void Tick() => Ticked?.Invoke(this, EventArgs.Empty);
}

class Window
{
    private readonly Clock clock;
    public int Ticks { get; private set; }
    public Window(Clock clock)
    {
        this.clock = clock;
        clock.Ticked += OnTick;
    }
    private void OnTick(object? sender, EventArgs e) => Ticks++;
    public void Close() => clock.Ticked -= OnTick;
}
