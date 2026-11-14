let rec depth n = if n = 0 then failwith "bottom" else 1 + depth (n - 1)

(* TODO: turn backtrace recording on before the failure happens. *)
let () =
  try ignore (depth 3)
  with Failure m -> Printf.printf "caught %s\n%s" m (Printexc.get_backtrace ())
