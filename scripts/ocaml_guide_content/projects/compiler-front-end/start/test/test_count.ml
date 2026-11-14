let rejects s = match Count.count_lets s with _ -> false | exception _ -> true

let () =
  assert (Count.count_lets "" = 0);
  assert (Count.count_lets "let x = 1" = 1);
  assert (Count.count_lets "let x = 1 type t = A let y = 2" = 2);
  assert (Count.count_lets "type t = A | B" = 0);
  assert (Count.count_lets "let rec f x = f x\nlet g = 3\nlet h = 4" = 3);
  assert (rejects "let = ");
  print_endline "count ok"
