string? text = args.Length > 0 ? args[0] : null;
Console.WriteLine(text.Length); // CS8602: dereference of a possibly null reference
