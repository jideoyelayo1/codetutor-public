let () =
  let q = Bq.create 2 in
  (* a consumer on an empty queue must block until something is pushed *)
  let result = ref None in
  let consumer = Thread.create (fun () -> result := Some (Bq.pop q)) () in
  Thread.delay 0.05;
  assert (!result = None);
  Bq.push q 42;
  Thread.join consumer;
  assert (!result = Some 42);
  (* a producer on a full queue must block until there is room *)
  Bq.push q 1;
  Bq.push q 2;
  let third_done = ref false in
  let producer = Thread.create (fun () -> Bq.push q 3; third_done := true) () in
  Thread.delay 0.05;
  assert (not !third_done);
  assert (Bq.pop q = 1);
  Thread.join producer;
  assert !third_done;
  assert (Bq.pop q = 2);
  assert (Bq.pop q = 3);
  (* many items through a small queue arrive in order and none are lost *)
  let total = ref 0 and count = 1000 in
  let reader = Thread.create (fun () -> for _ = 1 to count do total := !total + Bq.pop q done) () in
  for i = 1 to count do Bq.push q i done;
  Thread.join reader;
  assert (!total = count * (count + 1) / 2);
  print_endline "bq ok"
