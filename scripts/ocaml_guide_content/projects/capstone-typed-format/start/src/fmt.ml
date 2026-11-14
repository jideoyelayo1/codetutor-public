type ('a, 'r) fmt =
  | Lit : string -> ('r, 'r) fmt
  | Int : (int -> 'r, 'r) fmt
  | Str : (string -> 'r, 'r) fmt
  | Cat : ('a, 'b) fmt * ('b, 'r) fmt -> ('a, 'r) fmt

(* TODO: interpret the format in continuation-passing style.
   [acc] is the text produced so far; [k] receives the final text. *)
let kprintf : type a r. (string -> r) -> (a, r) fmt -> string -> a =
 fun _k _fmt _acc -> failwith "todo"

let sprintf f = kprintf Fun.id f ""
