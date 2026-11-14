(* TODO: a bounded BLOCKING queue. Protect the queue with a mutex and use two
   conditions: pop waits while the queue is empty, push waits while it is at
   capacity. Wait in a while loop and signal after every change. *)
type 'a t = { items : 'a Queue.t; capacity : int }

let create capacity = { items = Queue.create (); capacity }
let push q x = Queue.add x q.items
let pop q = match Queue.take_opt q.items with Some x -> x | None -> failwith "empty"
