try { Console.WriteLine(1); }
catch (Exception) { }
catch (FormatException) { } // CS0160: a previous catch clause already catches all exceptions of this type
