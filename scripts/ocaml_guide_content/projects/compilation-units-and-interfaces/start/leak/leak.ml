(* This code reaches inside the stack. It should stop compiling once the
   interface makes [Bounded_stack.t] abstract. *)
let () =
  let s = Bounded_stack.create 1 in
  print_int (List.length s.Bounded_stack.items)
