"""Original, deterministic executable companions to selected source studies.

These illustrate a concept, not a complete answer to each open design prompt.
Each tuple contains source and expected stdout; all code uses standard libraries.
"""
SNIPPETS = {
'rs-bindings': ('fn main() { let input = "12"; let input = input.len(); println!("{}", input); }', '2\n'),
'rs-primitives': ('fn main() { println!("{:?}", u8::try_from(300_i32)); println!("{:?}", u8::try_from(42_i32)); }', 'Err(TryFromIntError(()))\nOk(42)\n'),
'rs-control': ('fn main() { let result = (1..8).find(|n| n % 2 == 0); println!("{:?}", result); }', 'Some(2)\n'),
'rs-structs': ('#[derive(Debug)]\nenum Status { Pending, Ready(i32) }\nfn value(s: &Status) -> Option<i32> { match s { Status::Pending => None, Status::Ready(n) => Some(*n) } }\nfn main() { println!("{:?} {:?}", value(&Status::Pending), value(&Status::Ready(7))); }', 'None Some(7)\n'),
'rs-collections': ('fn main() { let text = "é"; println!("{} {}", text.len(), text.chars().count()); let values = vec![4, 5]; println!("{:?}", values.first()); }', '2 1\nSome(4)\n'),
'rs-modules': ('mod parser { pub fn doubled(s: &str) -> Result<i32, std::num::ParseIntError> { let n = s.parse::<i32>()?; Ok(n * 2) } }\nfn main() { println!("{:?}", parser::doubled("8")); }', 'Ok(16)\n'),
'rs-closures': ('fn main() { let text = String::from("owned"); let read = move || text.len(); println!("{} {}", read(), read()); }', '5 5\n'),
'rs-trait-objects': ('use std::fmt::Display;\nfn main() { let values: Vec<Box<dyn Display>> = vec![Box::new(12), Box::new("text")]; for value in values { println!("{}", value); } }', '12\ntext\n'),
'rs-associated': ('struct Down { next: u32 }\nimpl Iterator for Down { type Item = u32; fn next(&mut self) -> Option<Self::Item> { if self.next == 0 { None } else { let n = self.next; self.next -= 1; Some(n) } } }\nfn main() { println!("{:?}", Down { next: 3 }.collect::<Vec<_>>()); }', '[3, 2, 1]\n'),
'rs-smart': ('use std::rc::Rc;\nfn main() { let strong = Rc::new(9); let weak = Rc::downgrade(&strong); println!("{}", weak.upgrade().is_some()); drop(strong); println!("{}", weak.upgrade().is_some()); }', 'true\nfalse\n'),
'rs-patterns': ('fn label(n: Option<i32>) -> &\'static str { match n { None => "missing", Some(x) if x > 0 => "positive", Some(_) => "nonpositive" } }\nfn main() { println!("{} {} {}", label(None), label(Some(3)), label(Some(0))); }', 'missing positive nonpositive\n'),
'rs-macros': ('macro_rules! owned_values { ($($value:expr),* $(,)?) => { vec![$($value),*] }; }\nfn main() { let values = owned_values![2, 4, 6,]; println!("{:?}", values); }', '[2, 4, 6]\n'),
'rs-compatibility': ('struct Meters(u32);\nfn main() { let distance = Meters(12); println!("{}", distance.0); }', '12\n'),
'lean-universes': ('def keep {α : Type u} (x : α) : α := x\n#eval keep (7 : Nat)', '7\n'),
'lean-classes': ('structure Label where\n  value : String\ninstance : ToString Label where\n  toString x := x.value\n#eval toString (Label.mk "tag")', '"tag"\n'),
'lean-monads': ('def combine (a b : Option Nat) : Option Nat := do\n  let x ← a\n  let y ← b\n  pure (x + y)\n#eval combine (some 2) (some 3)\n#eval combine none (some 3)', 'some 5\nnone\n'),
'lean-indexed': ('def second : Fin 3 := ⟨1, by decide⟩\n#eval second.val\nexample : second.val < 3 := second.isLt', '1\n'),
'lean-termination': ('def down : Nat → List Nat\n  | 0 => []\n  | n + 1 => (n + 1) :: down n\n#eval down 3', '[3, 2, 1]\n'),
'lean-number-theory': ('#eval (2 : Nat) - 5\n#eval (2 : Int) - 5', '0\n-3\n'),
}
CPP = {
'cpp-types': ('int count{}; const int* read = &count; int* const fixed = &count; *fixed = 7; std::cout << *read << "\\n";', '7\n'),
'cpp-streams': ('std::istringstream input("4 8 stop"); int n{}; int total{}; while(input >> n) total += n; std::cout << total << "\\n";', '12\n'),
'cpp-algorithms': ('std::vector<int> a{1,2,3,4}; a.erase(std::remove_if(a.begin(), a.end(), [](int n){return n%2==0;}), a.end()); for(auto n:a) std::cout << n << " "; std::cout << "\\n";', '1 3 \n'),
'cpp-copy': ('std::vector<int> a{1,2}; auto b=a; b[0]=9; std::cout << a[0] << " " << b[0] << "\\n";', '1 9\n'),
'cpp-namespaces': ('std::cout << helper::twice(8) << "\\n";', '16\n'),
'cpp-constexpr': ('constexpr int n = square(4); static_assert(n == 16); std::cout << n << "\\n";', '16\n'),
'cpp-formatting': ('std::cout << std::boolalpha << true << " " << std::setfill(\'0\') << std::setw(4) << 7 << " " << std::setw(3) << 8 << "\\n";', 'true 0007 008\n'),
}
for key,(body,output) in CPP.items():
    source='#include <iostream>\n#include <vector>\n#include <algorithm>\n#include <sstream>\n#include <map>\n#include <string>\n#include <iomanip>\n#include <atomic>\n#include <thread>\nnamespace helper { int twice(int n) { return n*2; } }\nconstexpr int square(int n) { return n*n; }\nint main() { '+body+' }'
    SNIPPETS[key]=(source,output)
