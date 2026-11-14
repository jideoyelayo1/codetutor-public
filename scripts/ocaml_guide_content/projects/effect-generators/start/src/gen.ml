type _ Effect.t += Yield : int -> unit Effect.t

exception Stop

let yield n = Effect.perform (Yield n)

(* TODO: run [producer] under a deep handler, collect up to [n] yielded
   values, then stop the producer with [Effect.Deep.discontinue k Stop] so its
   cleanup runs. Return the values in yield order. *)
let take (_ : int) (_ : unit -> unit) : int list = []

let to_list producer = take max_int producer
