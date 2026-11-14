let slugify s =
  let buf = Buffer.create (String.length s) in
  let pending = ref false in
  String.iter
    (fun c ->
      let c = Char.lowercase_ascii c in
      if (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') then begin
        if !pending && Buffer.length buf > 0 then Buffer.add_char buf '-';
        pending := false;
        Buffer.add_char buf c
      end
      else pending := true)
    s;
  Buffer.contents buf
