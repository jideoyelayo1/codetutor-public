(** A stack of integers with a fixed capacity. *)

type t
(** The abstract stack type. Its representation is hidden. *)

val create : int -> t
(** [create capacity] is an empty stack that holds at most [capacity] elements. *)

val push : int -> t -> t option
(** [push x s] is [Some s'] with [x] on top, or [None] if [s] is already full. *)

val pop : t -> (int * t) option
(** [pop s] is [Some (x, s')] with the top element [x], or [None] if [s] is empty. *)

val size : t -> int
(** [size s] is the number of elements in [s]. *)
