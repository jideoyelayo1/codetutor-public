type error =
  | Empty
  | Stack_underflow
  | Bad_token of string
  | Leftover of int

let string_of_error = function
  | Empty -> "empty"
  | Stack_underflow -> "stack underflow"
  | Bad_token t -> "bad token " ^ t
  | Leftover n -> Printf.sprintf "%d values left" n

let eval input : (int, error) result =
  let apply op stack =
    match stack with
    | b :: a :: rest -> Ok (op a b :: rest)
    | _ -> Error Stack_underflow
  in
  let step stack tok =
    Result.bind stack (fun stack ->
        match tok with
        | "+" -> apply ( + ) stack
        | "-" -> apply ( - ) stack
        | "*" -> apply ( * ) stack
        | t -> (
            match int_of_string_opt t with
            | Some n -> Ok (n :: stack)
            | None -> Error (Bad_token t)))
  in
  let tokens =
    String.split_on_char ' ' input |> List.filter (fun t -> t <> "")
  in
  if tokens = [] then Error Empty
  else
    match List.fold_left step (Ok []) tokens with
    | Ok [ n ] -> Ok n
    | Ok stack -> Error (Leftover (List.length stack))
    | Error e -> Error e
