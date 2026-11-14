let () =
  assert (Fastsum.range 5 = [| 0; 1; 2; 3; 4 |]);
  assert (Fastsum.range 0 = [||]);
  assert (Fastsum.sum_ints [||] = 0);
  assert (Fastsum.sum_ints [| 1; 2; 3 |] = 6);
  assert (Fastsum.sum_ints [| -5; 5; 10 |] = 10);
  (* a large array lives in the major heap; the stub must still read it *)
  assert (Fastsum.sum_ints (Fastsum.range 100_000) = 4_999_950_000);
  print_endline "fastsum ok"
