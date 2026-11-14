let () =
  let lines = [ "a b a"; "c a"; ""; "b b c"; "d" ] in
  let expect = [ ("a", 3); ("b", 3); ("c", 2); ("d", 1) ] in
  assert (Pipeline.count ~workers:1 lines = expect);
  assert (Pipeline.count ~workers:3 lines = expect);
  (* more workers than lines: some chunks are empty *)
  assert (Pipeline.count ~workers:8 lines = expect);
  assert (Pipeline.count ~workers:4 [] = []);
  (* an invalid worker count is rejected up front, not with Division_by_zero *)
  assert (
    match Pipeline.count ~workers:0 lines with
    | _ -> false
    | exception Invalid_argument _ -> true);
  (* a failing worker must not leave the others unjoined *)
  Atomic.set Pipeline.finished 0;
  let process line =
    if line = "BAD" then failwith "boom" else Pipeline.default_process line
  in
  (match
     Pipeline.count ~workers:3 ~process [ "x"; "BAD"; "y"; "z"; "w"; "v" ]
   with
  | _ -> assert false
  | exception Failure m -> assert (m = "boom"));
  assert (Atomic.get Pipeline.finished = 3);
  print_endline "pipeline ok"
