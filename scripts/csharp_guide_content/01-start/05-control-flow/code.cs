int score = 74;
if (score >= 90) Console.WriteLine("A");
else if (score >= 70) Console.WriteLine("C");
else Console.WriteLine("F");

for (int i = 1; i <= 15; i++)
{
    string word = (i % 3, i % 5) switch { (0, 0) => "FizzBuzz", (0, _) => "Fizz", (_, 0) => "Buzz", _ => i.ToString() };
    Console.Write(word + " ");
}
Console.WriteLine();

string day = "Sunday";
switch (day)
{
    case "Saturday":
    case "Sunday":
        Console.WriteLine("weekend");
        break;
    default:
        Console.WriteLine("weekday");
        break;
}

int[] numbers = [1, 3, 5, 7, 9];
bool found = false;
for (int a = 0; a < numbers.Length && !found; a++)
    for (int b = a + 1; b < numbers.Length; b++)
        if (numbers[a] + numbers[b] == 10)
        {
            Console.WriteLine($"first pair summing to 10: {numbers[a]} + {numbers[b]}");
            found = true;
            break;
        }

int n = 3;
Console.Write("countdown: ");
do { Console.Write(n + " "); n--; } while (n > 0);
Console.WriteLine();
