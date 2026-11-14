let () =
  let s = Bounded_stack.create 2 in
  match Bounded_stack.push 1 s with
  | None -> print_endline "unexpected"
  | Some s -> (
      match Bounded_stack.push 2 s with
      | None -> print_endline "unexpected"
      | Some s ->
          Printf.printf "%d %b\n" (Bounded_stack.size s)
            (Bounded_stack.push 3 s <> None))
