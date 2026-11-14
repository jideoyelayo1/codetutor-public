(* TODO: implement these with the Unix module.
   file_size    : size in bytes; raises Unix.Unix_error (ENOENT, _, _) if missing.
   list_dir     : entry names, sorted, without "." and "..".
   copy_file    : copy src to dst in 4096-byte chunks; close both descriptors
                  on every path, and handle partial reads and writes. *)
let file_size (_ : string) : int = failwith "todo"
let list_dir (_ : string) : string list = failwith "todo"
let copy_file (_ : string) (_ : string) : unit = failwith "todo"
