type _ Effect.t += Yield : int -> unit Effect.t

exception Stop

let yield n = Effect.perform (Yield n)

let take n producer : int list =
  let acc = ref [] and count = ref 0 in
  if n > 0 then
    Effect.Deep.match_with producer ()
      {
        retc = (fun () -> ());
        exnc = (function Stop -> () | e -> raise e);
        effc =
          (fun (type a) (eff : a Effect.t) ->
            match eff with
            | Yield v ->
                Some
                  (fun (k : (a, _) Effect.Deep.continuation) ->
                    acc := v :: !acc;
                    incr count;
                    if !count >= n then Effect.Deep.discontinue k Stop
                    else Effect.Deep.continue k ())
            | _ -> None);
      };
  List.rev !acc

let to_list producer = take max_int producer
