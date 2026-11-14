type t = { name : string; port : int; tags : string list }

let to_json c : Yojson.Safe.t =
  `Assoc
    [ ("name", `String c.name);
      ("port", `Int c.port);
      ("tags", `List (List.map (fun s -> `String s) c.tags)) ]

let parse (text : string) : (t, string) result =
  match Yojson.Safe.from_string text with
  | exception Yojson.Json_error message -> Error message
  | json -> (
      let open Yojson.Safe.Util in
      try
        Ok
          { name = member "name" json |> to_string;
            port = member "port" json |> to_int;
            tags = member "tags" json |> to_list |> List.map to_string }
      with Type_error (message, _) -> Error message)
