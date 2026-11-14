type error =
  | Empty
  | Stack_underflow
  | Bad_token of string
  | Leftover of int

let string_of_error = function
  | Empty -> "empty"
  | Stack_underflow -> "stack underflow"
  | Bad_token t -> "bad token " ^ t
  | Leftover n -> Printf.sprintf "%d values left" n

(* TODO: evaluate a space-separated reverse-polish expression. *)
let eval (_ : string) : (int, error) result = Error Empty
