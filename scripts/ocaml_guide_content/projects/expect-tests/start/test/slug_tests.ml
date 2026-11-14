let%expect_test "lowercases and hyphenates" =
  print_endline (Slug.slugify "Hello World");
  [%expect {| hello-world |}]

let%expect_test "drops punctuation" =
  print_endline (Slug.slugify "OCaml: fun & fast!");
  [%expect {| ocaml-fun-fast |}]

let%expect_test "collapses repeats and trims" =
  print_endline (Slug.slugify "  a   b  ");
  [%expect {| a-b |}]
