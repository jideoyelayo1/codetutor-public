%token <int> NUM
%token PLUS MINUS STAR LPAREN RPAREN EOF

(* TODO: add the binary operators' precedence above UMINUS. Later lines bind
   tighter: first %left PLUS MINUS, then %left STAR. *)
%nonassoc UMINUS

%start <Ast.expr> main

%%

main:
  | e = expr EOF { e }

expr:
  | n = NUM { Ast.Num n }
  | a = expr PLUS b = expr { Ast.Add (a, b) }
  | a = expr MINUS b = expr { Ast.Sub (a, b) }
  | a = expr STAR b = expr { Ast.Mul (a, b) }
  | MINUS e = expr %prec UMINUS { Ast.Neg e }
  | LPAREN e = expr RPAREN { e }
