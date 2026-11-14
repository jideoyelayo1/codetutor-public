open Core

let top ~n text : (string * int) list =
  String.split_on_chars text ~on:[ ' '; '\n'; '\t' ]
  |> List.filter ~f:(fun w -> not (String.is_empty w))
  |> List.map ~f:String.lowercase
  |> List.fold
       ~init:(Map.empty (module String))
       ~f:(fun counts word ->
         Map.update counts word ~f:(function None -> 1 | Some c -> c + 1))
  |> Map.to_alist
  |> List.sort ~compare:(fun (w1, c1) (w2, c2) ->
         match Int.compare c2 c1 with 0 -> String.compare w1 w2 | c -> c)
  |> fun sorted -> List.take sorted n
