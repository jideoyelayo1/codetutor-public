type t = { name : string; port : int; tags : string list }

let to_json c : Yojson.Safe.t =
  `Assoc
    [ ("name", `String c.name);
      ("port", `Int c.port);
      ("tags", `List (List.map (fun s -> `String s) c.tags)) ]

(* TODO: parse a JSON object with "name" (string), "port" (int) and "tags"
   (list of strings). Return Error with a message for invalid JSON or a
   missing / wrongly typed field. *)
let parse (_ : string) : (t, string) result = Error "todo"
