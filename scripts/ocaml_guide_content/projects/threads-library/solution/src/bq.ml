type 'a t = {
  items : 'a Queue.t;
  capacity : int;
  m : Mutex.t;
  not_empty : Condition.t;
  not_full : Condition.t;
}

let create capacity =
  { items = Queue.create (); capacity; m = Mutex.create (); not_empty = Condition.create (); not_full = Condition.create () }

let push q x =
  Mutex.protect q.m (fun () ->
      while Queue.length q.items >= q.capacity do
        Condition.wait q.not_full q.m
      done;
      Queue.add x q.items;
      Condition.signal q.not_empty)

let pop q =
  Mutex.protect q.m (fun () ->
      while Queue.is_empty q.items do
        Condition.wait q.not_empty q.m
      done;
      let x = Queue.take q.items in
      Condition.signal q.not_full;
      x)
