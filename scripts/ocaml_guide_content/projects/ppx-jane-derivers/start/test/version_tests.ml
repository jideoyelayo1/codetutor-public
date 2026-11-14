open Core

let parse s = Or_error.ok_exn (Version.of_string s)

let%expect_test "parse and print as a sexp" =
  print_s [%sexp (Version.of_string "1.2.3" : Version.t Or_error.t)];
  [%expect {| (Ok ((major 1) (minor 2) (patch 3))) |}];
  printf "%b %b\n"
    (Or_error.is_error (Version.of_string "1.2"))
    (Or_error.is_error (Version.of_string "1.-2.3"));
  [%expect {| true true |}]

let%expect_test "ordering is numeric, not textual" =
  let sorted =
    List.map [ "1.10.0"; "1.2.0"; "0.9.9" ] ~f:parse
    |> List.sort ~compare:Version.compare
    |> List.map ~f:Version.to_string
  in
  print_s [%sexp (sorted : string list)];
  [%expect {| (0.9.9 1.2.0 1.10.0) |}];
  printf "%b\n" Version.(parse "1.2.0" < parse "1.10.0");
  [%expect {| true |}]

let%expect_test "bump_minor resets patch" =
  print_endline (Version.to_string (Version.bump_minor (parse "1.2.3")));
  [%expect {| 1.3.0 |}]

let%expect_test "equal and hash agree" =
  let a = parse "2.0.1" and b = parse "2.0.1" in
  printf "%b %b\n" (Version.equal a b) (Version.hash a = Version.hash b);
  [%expect {| true true |}]
