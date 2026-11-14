open Core

(* TODO: parse "name=int". Missing '=' or a non-integer value is an error. *)
let parse_entry (_ : string) : (string * int) Or_error.t =
  Or_error.error_string "todo"

(* TODO: parse every entry (stop at the first error), add up values that
   share a name, and return the pairs sorted by name. *)
let totals (_ : string list) : (string * int) list Or_error.t =
  Or_error.error_string "todo"
