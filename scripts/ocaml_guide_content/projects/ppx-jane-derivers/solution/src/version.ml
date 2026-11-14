open Core

module T = struct
  type t = { major : int; minor : int; patch : int }
  [@@deriving sexp, compare, equal, hash]
end

include T
include Comparable.Make (T)

let of_string s : t Or_error.t =
  let part p = Option.try_with (fun () -> Int.of_string p) in
  match List.map (String.split s ~on:'.') ~f:part with
  | [ Some major; Some minor; Some patch ]
    when Int.(major >= 0 && minor >= 0 && patch >= 0) ->
      Ok { major; minor; patch }
  | _ -> Or_error.errorf "not a version: %S" s

let bump_minor t = { t with minor = t.minor + 1; patch = 0 }
let to_string t = sprintf "%d.%d.%d" t.major t.minor t.patch
