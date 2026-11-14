(* Number of workers that have finished, whether they succeeded or raised. *)
let finished = Atomic.make 0

let default_process line =
  String.split_on_char ' ' line |> List.filter (fun w -> w <> "")

let bump table word by =
  Hashtbl.replace table word
    (by + Option.value (Hashtbl.find_opt table word) ~default:0)

let count ~workers ?(process = default_process) lines :
    (string * int) list =
  if workers < 1 then invalid_arg "Pipeline.count: workers must be at least 1";
  let lines = Array.of_list lines in
  let n = Array.length lines in
  let size = max 1 ((n + workers - 1) / workers) in
  let work d () =
    Fun.protect
      ~finally:(fun () -> Atomic.incr finished)
      (fun () ->
        let table = Hashtbl.create 64 in
        for i = min n (d * size) to min n ((d + 1) * size) - 1 do
          List.iter (fun w -> bump table w 1) (process lines.(i))
        done;
        table)
  in
  (* If a spawn fails partway, join what already started before re-raising. *)
  let started = ref [] in
  (try
     for d = 0 to workers - 1 do
       started := Domain.spawn (work d) :: !started
     done
   with e ->
     List.iter (fun d -> try ignore (Domain.join d) with _ -> ()) !started;
     raise e);
  let domains = List.rev !started in
  (* Join every domain before reporting any failure. *)
  let outcomes =
    List.map (fun d -> try Ok (Domain.join d) with e -> Error e) domains
  in
  (match
     List.find_map (function Error e -> Some e | Ok _ -> None) outcomes
   with
  | Some e -> raise e
  | None -> ());
  let total = Hashtbl.create 64 in
  List.iter
    (function
      | Ok table -> Hashtbl.iter (fun w c -> bump total w c) table
      | Error _ -> ())
    outcomes;
  Hashtbl.fold (fun w c acc -> (w, c) :: acc) total [] |> List.sort compare
