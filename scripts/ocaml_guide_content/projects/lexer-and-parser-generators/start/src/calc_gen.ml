module Ast = Ast

let parse s = Parser.main Lexer.token (Lexing.from_string s)

let rec eval = function
  | Ast.Num n -> n
  | Ast.Add (a, b) -> eval a + eval b
  | Ast.Sub (a, b) -> eval a - eval b
  | Ast.Mul (a, b) -> eval a * eval b
  | Ast.Neg e -> - eval e

let calc s = eval (parse s)
