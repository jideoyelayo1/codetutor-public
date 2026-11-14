List<Cat> cats = [new Cat("Tom"), new Cat("Kit")];
IEnumerable<Animal> animals = cats;                 // covariance (IEnumerable<out T>)
foreach (var a in animals) Console.Write(a.Name + " ");
Console.WriteLine();

Action<Animal> describe = a => Console.WriteLine($"animal: {a.Name}");
Action<Cat> describeCat = describe;                 // contravariance (Action<in T>)
describeCat(new Cat("Tom"));

Func<Cat> makeCat = () => new Cat("New");
Func<Animal> makeAnimal = makeCat;                  // covariant result
Console.WriteLine(makeAnimal().Name);

IComparer<Animal> byName = Comparer<Animal>.Create((x, y) => string.CompareOrdinal(x.Name, y.Name));
cats.Sort(byName);                                  // IComparer<in T>
Console.WriteLine(string.Join(",", cats.Select(c => c.Name)));

Animal[] array = new Cat[1];                        // array covariance is unsafe
try { array[0] = new Dog("Rex"); }
catch (ArrayTypeMismatchException) { Console.WriteLine("array covariance failed at runtime"); }

record Animal(string Name);
record Cat(string Name) : Animal(Name);
record Dog(string Name) : Animal(Name);
