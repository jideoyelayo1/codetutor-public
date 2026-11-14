(* TODO: parse [source] with Parse.implementation and count the top-level
   items whose [pstr_desc] is Pstr_value (a "let" binding). Syntax errors
   raise from the parser and should be left to propagate. *)
let count_lets (_ : string) : int = 0
