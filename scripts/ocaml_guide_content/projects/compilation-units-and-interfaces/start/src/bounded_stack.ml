type t = { capacity : int; items : int list }

let create capacity = { capacity; items = [] }

let push x s =
  if List.length s.items >= s.capacity then None
  else Some { s with items = x :: s.items }

let pop s =
  match s.items with [] -> None | x :: rest -> Some (x, { s with items = rest })

let size s = List.length s.items
