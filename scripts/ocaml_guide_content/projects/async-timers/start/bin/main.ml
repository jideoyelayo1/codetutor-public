open Async

let command =
  Command.async ~summary:"Run three timers"
    (Command.Param.return (fun () -> Timers.run ()))

let () = Command_unix.run command
