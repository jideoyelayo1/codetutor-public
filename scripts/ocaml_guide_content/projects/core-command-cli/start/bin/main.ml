open Core

let command =
  Command.basic ~summary:"Print the most frequent words"
    (let%map_open.Command n =
       flag "-n" (optional_with_default 3 int) ~doc:"N how many words to show"
     and text = anon ("TEXT" %: string) in
     fun () ->
       List.iter (Wordfreq.top ~n text) ~f:(fun (word, count) ->
           printf "%s %d\n" word count))

let () = Command_unix.run command
