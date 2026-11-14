var clock = new Clock();
using (clock.Subscribe((_, _) => { }))
{
    Console.WriteLine(clock.SubscriberCount);
}
Console.WriteLine(clock.SubscriberCount);

class Clock
{
    private event EventHandler? Ticked;
    public int SubscriberCount => Ticked?.GetInvocationList().Length ?? 0;
    public IDisposable Subscribe(EventHandler handler)
    {
        Ticked += handler;
        return new Subscription(() => Ticked -= handler);
    }
    private sealed class Subscription(Action unsubscribe) : IDisposable
    {
        private Action? unsubscribe = unsubscribe;
        public void Dispose()
        {
            unsubscribe?.Invoke();
            unsubscribe = null;   // idempotent: a second Dispose does nothing
        }
    }
}
