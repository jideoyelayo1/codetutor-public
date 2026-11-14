let naturals () =
  let i = ref 0 in
  while true do
    Gen.yield !i;
    incr i
  done

let () =
  assert (Gen.take 5 naturals = [ 0; 1; 2; 3; 4 ]);
  assert (Gen.to_list (fun () -> List.iter Gen.yield [ 3; 1; 2 ]) = [ 3; 1; 2 ]);
  assert (Gen.take 0 naturals = []);
  (* Stopping early must unwind the producer so its cleanup runs. *)
  let cleaned = ref 0 in
  let guarded () = Fun.protect ~finally:(fun () -> incr cleaned) naturals in
  assert (Gen.take 3 guarded = [ 0; 1; 2 ]);
  assert (!cleaned = 1);
  print_endline "gen ok"
