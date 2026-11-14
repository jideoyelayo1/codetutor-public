let file_size path = (Unix.stat path).Unix.st_size

let list_dir dir =
  let handle = Unix.opendir dir in
  Fun.protect
    ~finally:(fun () -> Unix.closedir handle)
    (fun () ->
      let rec go acc =
        match Unix.readdir handle with
        | name -> go (if name = "." || name = ".." then acc else name :: acc)
        | exception End_of_file -> List.sort compare acc
      in
      go [])

let copy_file src dst =
  let ifd = Unix.openfile src [ Unix.O_RDONLY ] 0 in
  Fun.protect
    ~finally:(fun () -> Unix.close ifd)
    (fun () ->
      let ofd = Unix.openfile dst [ Unix.O_WRONLY; Unix.O_CREAT; Unix.O_TRUNC ] 0o644 in
      Fun.protect
        ~finally:(fun () -> Unix.close ofd)
        (fun () ->
          let buf = Bytes.create 4096 in
          let rec copy () =
            let n = Unix.read ifd buf 0 4096 in
            if n > 0 then begin
              let written = ref 0 in
              while !written < n do
                written := !written + Unix.write ofd buf !written (n - !written)
              done;
              copy ()
            end
          in
          copy ()))
