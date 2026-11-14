using System.Reflection;

Console.WriteLine(Describe(Level.Low));
Console.WriteLine(Describe(Level.High));

static string Describe(Enum value) =>
    value.GetType().GetField(value.ToString())?.GetCustomAttribute<DescriptionAttribute>()?.Text ?? value.ToString();

[AttributeUsage(AttributeTargets.Field)]
sealed class DescriptionAttribute(string text) : Attribute { public string Text => text; }

enum Level { [Description("Very low")] Low, High }
