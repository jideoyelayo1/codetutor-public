using System.Reflection;
using System.Runtime.InteropServices;

Console.WriteLine($"runtime major version: {Environment.Version.Major}");
Console.WriteLine(RuntimeInformation.FrameworkDescription.StartsWith(".NET 10"));
var assembly = Assembly.GetExecutingAssembly();
Console.WriteLine(assembly.GetName().Name);
Console.WriteLine(assembly.GetCustomAttribute<System.Runtime.Versioning.TargetFrameworkAttribute>()?.FrameworkName);
#if DEBUG
Console.WriteLine("Debug configuration");
#else
Console.WriteLine("Release configuration");
#endif
Console.WriteLine(System.Runtime.CompilerServices.RuntimeFeature.IsDynamicCodeSupported ? "JIT available (not Native AOT)" : "Native AOT");
