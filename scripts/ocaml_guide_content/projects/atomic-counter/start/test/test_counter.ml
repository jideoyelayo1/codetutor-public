let () =
  let c = Counter.create () in
  let worker () =
    for _ = 1 to 200_000 do
      Counter.incr c
    done
  in
  let domains = List.init 4 (fun _ -> Domain.spawn worker) in
  List.iter Domain.join domains;
  assert (Counter.get c = 800_000);
  print_endline "counter ok"
