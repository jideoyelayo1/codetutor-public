type t = int Atomic.t

let create () = Atomic.make 0
let incr = Atomic.incr
let get = Atomic.get
