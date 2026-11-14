(* TODO: this plain ref loses updates when several domains increment it.
   Rebuild it on Atomic so incr is indivisible. *)
type t = int ref

let create () = ref 0
let incr t = t := !t + 1
let get t = !t
