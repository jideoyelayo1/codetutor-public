{
  open Parser
}

rule token = parse
  | [' ' '\t' '\n'] { token lexbuf }
  | ['0'-'9']+ as n { NUM (int_of_string n) }
  | '+' { PLUS }
  | '-' { MINUS }
  | '*' { STAR }
  | '(' { LPAREN }
  | ')' { RPAREN }
  | eof { EOF }
  | _ as c { failwith (Printf.sprintf "unexpected character %C" c) }
