type ('a, 'r) fmt =
  | Lit : string -> ('r, 'r) fmt
  | Int : (int -> 'r, 'r) fmt
  | Str : (string -> 'r, 'r) fmt
  | Cat : ('a, 'b) fmt * ('b, 'r) fmt -> ('a, 'r) fmt

let rec kprintf : type a r. (string -> r) -> (a, r) fmt -> string -> a =
 fun k fmt acc ->
  match fmt with
  | Lit s -> k (acc ^ s)
  | Int -> fun n -> k (acc ^ string_of_int n)
  | Str -> fun s -> k (acc ^ s)
  | Cat (f1, f2) -> kprintf (fun acc' -> kprintf k f2 acc') f1 acc

let sprintf f = kprintf Fun.id f ""
