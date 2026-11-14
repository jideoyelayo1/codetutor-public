let numbers s =
  let re = Str.regexp "[0-9]+" in
  let rec go pos acc =
    match Str.search_forward re s pos with
    | start ->
        let m = Str.matched_string s in
        go (start + String.length m) (int_of_string m :: acc)
    | exception Not_found -> List.rev acc
  in
  go 0 []

let words s = Str.split (Str.regexp "[ \t\n]+") s
let squeeze s = String.trim (Str.global_replace (Str.regexp "[ \t]+") " " s)
