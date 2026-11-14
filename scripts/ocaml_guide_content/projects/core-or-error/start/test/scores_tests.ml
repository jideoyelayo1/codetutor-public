open Core

let%expect_test "parse_entry" =
  print_s [%sexp (Scores.parse_entry "ada=3" : (string * int) Or_error.t)];
  [%expect {| (Ok (ada 3)) |}];
  print_endline (Or_error.is_error (Scores.parse_entry "ada") |> Bool.to_string);
  [%expect {| true |}];
  print_endline (Or_error.is_error (Scores.parse_entry "ada=x") |> Bool.to_string);
  [%expect {| true |}]

let%expect_test "totals sums by name and sorts" =
  print_s
    [%sexp
      (Scores.totals [ "b=2"; "a=1"; "b=5" ] : (string * int) list Or_error.t)];
  [%expect {| (Ok ((a 1) (b 7))) |}]

let%expect_test "totals reports the first bad entry" =
  (match Scores.totals [ "a=1"; "oops"; "b=2" ] with
  | Ok _ -> print_endline "unexpected success"
  | Error e -> print_endline (Error.to_string_hum e));
  [%expect {| missing '=' in "oops" |}]
