open Core

(* TODO: derive sexp, compare, equal and hash, then include Comparable.Make. *)
type t = { major : int; minor : int; patch : int }

(* TODO: parse "major.minor.patch"; every part must be a non-negative int. *)
let of_string (_ : string) : t Or_error.t = Or_error.error_string "todo"

(* TODO: increment minor and reset patch to 0. *)
let bump_minor t = t
let to_string t = sprintf "%d.%d.%d" t.major t.minor t.patch
