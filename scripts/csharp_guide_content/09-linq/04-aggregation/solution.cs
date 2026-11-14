(string Student, int Score)[] scores = [("ada", 70), ("bob", 85), ("ada", 92), ("cy", 60), ("bob", 80)];
var best = scores.AggregateBy(s => s.Student, 0, (max, s) => Math.Max(max, s.Score));
foreach (var (student, top) in best.OrderBy(p => p.Key)) Console.WriteLine($"{student} {top}");
Console.WriteLine(scores.MaxBy(s => s.Score).Student);
