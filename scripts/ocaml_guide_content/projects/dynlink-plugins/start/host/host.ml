let () =
  let path = Sys.argv.(1) in
  (try Dynlink.loadfile path
   with Dynlink.Error e ->
     prerr_endline ("cannot load " ^ path ^ ": " ^ Dynlink.error_message e);
     exit 2);
  List.iter
    (fun (name, f) -> Printf.printf "%s: %d\n" name (f 21))
    (List.rev !Registry.plugins)
