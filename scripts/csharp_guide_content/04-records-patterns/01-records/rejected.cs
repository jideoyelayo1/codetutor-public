var p = new Person("Ada");
p.Name = "Bob"; // CS8852: init-only property can only be assigned in an initializer
record Person(string Name);
