(* TODO: make [t] abstract and document each function. *)
type t = { capacity : int; items : int list }

val create : int -> t
val push : int -> t -> t option
val pop : t -> (int * t) option
val size : t -> int
