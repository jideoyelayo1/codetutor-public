let write path s = Out_channel.with_open_bin path (fun oc -> output_string oc s)
let read path = In_channel.with_open_bin path In_channel.input_all

(* Number of descriptors this process has open (/dev/fd is available on macOS and Linux). *)
let open_descriptors () = Array.length (Sys.readdir "/dev/fd")

let () =
  let dir = Filename.temp_dir "fileops" "" in
  let a = Filename.concat dir "a.txt" and b = Filename.concat dir "b.txt" in
  let content = String.make 10_000 'x' in
  write a content;
  assert (Fileops.file_size a = 10_000);
  Fileops.copy_file a b;
  assert (Fileops.file_size b = 10_000);
  assert (read b = content);
  assert (Fileops.list_dir dir = [ "a.txt"; "b.txt" ]);
  (match Fileops.file_size (Filename.concat dir "missing") with
  | _ -> assert false
  | exception Unix.Unix_error (Unix.ENOENT, _, _) -> ());
  (* Failing and succeeding copies must leave no descriptor open. *)
  let before = open_descriptors () in
  for _ = 1 to 200 do
    match Fileops.copy_file (Filename.concat dir "missing") b with
    | () -> assert false
    | exception Unix.Unix_error _ -> ()
  done;
  assert (open_descriptors () = before);
  (* The source opens, then the destination fails: the source must still be closed. *)
  for _ = 1 to 200 do
    match Fileops.copy_file a (Filename.concat dir "no-such-directory/out.txt") with
    | () -> assert false
    | exception Unix.Unix_error _ -> ()
  done;
  assert (open_descriptors () = before);
  for _ = 1 to 200 do
    Fileops.copy_file a b
  done;
  assert (open_descriptors () = before);
  ignore (Fileops.list_dir dir);
  assert (open_descriptors () = before);
  Sys.remove a;
  Sys.remove b;
  Sys.rmdir dir;
  print_endline "fileops ok"
