let () =
  let a = Array.init 1000 (fun i -> i + 1) in
  assert (Psum.sum ~domains:1 a = 500_500);
  assert (Psum.sum ~domains:4 a = 500_500);
  (* 1000 does not divide evenly by 7, so the last chunk is short. *)
  assert (Psum.sum ~domains:7 a = 500_500);
  assert (Psum.sum ~domains:4 [||] = 0);
  (* more domains than elements: some chunks are empty *)
  assert (Psum.sum ~domains:8 [| 5 |] = 5);
  (* an invalid domain count is rejected up front, not with Division_by_zero *)
  assert (
    match Psum.sum ~domains:0 a with
    | _ -> false
    | exception Invalid_argument _ -> true);
  print_endline "psum ok"
