(* TODO: this plug-in should double its input, but it returns it unchanged. *)
let () = Registry.register "double" (fun x -> x)
