let () =
  let n = Tracing.count_gc_events () in
  (* A full major collection runs several runtime phases. *)
  assert (n > 0);
  print_endline "runtime events seen"
