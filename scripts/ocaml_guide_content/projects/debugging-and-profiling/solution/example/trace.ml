let rec depth n = if n = 0 then failwith "bottom" else 1 + depth (n - 1)

let () =
  Printexc.record_backtrace true;
  try ignore (depth 3)
  with Failure m -> Printf.printf "caught %s\n%s" m (Printexc.get_backtrace ())
