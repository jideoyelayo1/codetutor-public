let%expect_test "shout upper-cases at compile time" =
  print_endline [%shout "hello"];
  [%expect {| HELLO |}];
  print_endline [%shout "mixed Case 1"];
  [%expect {| MIXED CASE 1 |}]
