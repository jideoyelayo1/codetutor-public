open Core
open Async

let delayed name ms =
  let%map () = after (Time_float.Span.of_ms ms) in
  print_endline name;
  name

let report results = printf "results: %s\n" (String.concat ~sep:"," results)

let run () =
  let%bind results =
    Deferred.all
      [ delayed "slow" 200.; delayed "fast" 20.; delayed "medium" 100. ]
  in
  report results;
  return ()
