open Core
open Async

(* Waits [ms] milliseconds, prints its name when it finishes, returns the name. *)
let delayed name ms =
  let%map () = after (Time_float.Span.of_ms ms) in
  print_endline name;
  name

let report results = printf "results: %s\n" (String.concat ~sep:"," results)

(* TODO: start all three timers at once with Deferred.all instead of waiting
   for each one before starting the next. *)
let run () =
  let%bind a = delayed "slow" 200. in
  let%bind b = delayed "fast" 20. in
  let%bind c = delayed "medium" 100. in
  report [ a; b; c ];
  return ()
