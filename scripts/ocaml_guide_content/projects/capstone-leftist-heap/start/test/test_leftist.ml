module H = Leftist.Make (Int)

let () =
  assert (H.find_min H.empty = None);
  assert (H.delete_min H.empty = None);
  assert (H.to_sorted_list (H.of_list [ 3; 1; 2 ]) = [ 1; 2; 3 ]);
  assert (H.to_sorted_list (H.of_list [ 2; 2; 1; 2 ]) = [ 1; 2; 2; 2 ]);
  (* persistence: operations never change the heap they were given *)
  let h = H.of_list [ 3; 1; 2 ] in
  let _ = H.delete_min h in
  let _ = H.insert 0 h in
  assert (H.find_min h = Some 1);
  assert (H.to_sorted_list h = [ 1; 2; 3 ]);
  (* random inputs must agree with List.sort *)
  Random.init 42;
  for _ = 1 to 200 do
    let l = List.init (Random.int 40) (fun _ -> Random.int 20) in
    assert (H.to_sorted_list (H.of_list l) = List.sort compare l)
  done;
  (* merging two heaps keeps every element *)
  let a = H.of_list [ 5; 1; 9 ] and b = H.of_list [ 4; 2 ] in
  assert (H.to_sorted_list (H.merge a b) = [ 1; 2; 4; 5; 9 ]);
  print_endline "leftist ok"
