Pet pet = new Cat("Tom");
Console.WriteLine(pet switch { Cat c => c.Name });   // CS8509: Dog is not handled
public record Cat(string Name);
public record Dog(string Name);
public union Pet(Cat, Dog);
