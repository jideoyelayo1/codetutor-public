(* TODO: the recursive call below is not a tail call (n + ... happens after it
   returns), so [@tailcall] is a false promise. Rewrite sum with an accumulator
   so the recursive call really is the last thing the function does. *)
let rec sum n = if n = 0 then 0 else n + (sum [@tailcall]) (n - 1)
