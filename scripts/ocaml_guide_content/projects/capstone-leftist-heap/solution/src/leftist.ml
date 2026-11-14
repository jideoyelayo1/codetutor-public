module type ORDERED = sig
  type t

  val compare : t -> t -> int
end

module Make (O : ORDERED) = struct
  type elt = O.t
  type t = E | T of int * elt * t * t (* rank, root, left, right *)

  let empty = E
  let is_empty = function E -> true | T _ -> false
  let rank = function E -> 0 | T (r, _, _, _) -> r

  (* Build a node, putting the higher-rank child on the left. *)
  let make x a b =
    if rank a >= rank b then T (rank b + 1, x, a, b)
    else T (rank a + 1, x, b, a)

  let rec merge h1 h2 =
    match (h1, h2) with
    | E, h | h, E -> h
    | T (_, x, a1, b1), T (_, y, a2, b2) ->
        if O.compare x y <= 0 then make x a1 (merge b1 h2)
        else make y a2 (merge h1 b2)

  let insert x h = merge (T (1, x, E, E)) h
  let find_min = function E -> None | T (_, x, _, _) -> Some x
  let delete_min = function E -> None | T (_, _, a, b) -> Some (merge a b)
  let of_list l = List.fold_left (fun h x -> insert x h) empty l

  let to_sorted_list h =
    let rec go acc h =
      match (find_min h, delete_min h) with
      | Some x, Some rest -> go (x :: acc) rest
      | _ -> List.rev acc
    in
    go [] h
end
