open Core

let parse_entry s : (string * int) Or_error.t =
  match String.lsplit2 s ~on:'=' with
  | None -> Or_error.errorf "missing '=' in %S" s
  | Some (name, value) -> (
      match Int.of_string value with
      | n -> Ok (name, n)
      | exception _ -> Or_error.errorf "bad number %S in %S" value s)

let totals entries : (string * int) list Or_error.t =
  let open Or_error.Let_syntax in
  let%map pairs = Or_error.all (List.map entries ~f:parse_entry) in
  Map.of_alist_reduce (module String) pairs ~f:( + ) |> Map.to_alist
