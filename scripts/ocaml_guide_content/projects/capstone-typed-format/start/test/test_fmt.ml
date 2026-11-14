open Fmt

let () =
  assert (sprintf (Lit "hello") = "hello");
  assert (sprintf Int 42 = "42");
  assert (sprintf Str "ocaml" = "ocaml");
  let f = Cat (Lit "x=", Cat (Int, Cat (Lit ", name=", Str))) in
  assert (sprintf f 3 "bob" = "x=3, name=bob");
  (* arguments are consumed left to right *)
  assert (sprintf (Cat (Str, Cat (Lit "-", Str))) "a" "b" = "a-b");
  (* a format can finish with a different continuation *)
  assert (kprintf String.length (Cat (Lit "abc", Int)) "" 12345 = 8);
  print_endline "fmt ok"
