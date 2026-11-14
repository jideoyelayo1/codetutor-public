(* Number of workers that have finished, whether they succeeded or raised. *)
let finished = Atomic.make 0

let default_process line =
  String.split_on_char ' ' line |> List.filter (fun w -> w <> "")

(* TODO: split [lines] into [workers] contiguous chunks, run one Domain per
   chunk counting words into a private Hashtbl (call [Atomic.incr finished] in
   a Fun.protect ~finally), join EVERY domain capturing Ok/Error, re-raise the
   first error only after all are joined, then merge the tables into a list of
   (word, count) sorted by word. *)
let count ~workers ?(process = default_process) lines =
  ignore (workers, process, lines);
  ([] : (string * int) list)
