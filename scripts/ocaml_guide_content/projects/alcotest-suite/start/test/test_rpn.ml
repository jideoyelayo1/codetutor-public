let error_t =
  Alcotest.testable
    (fun fmt e -> Format.pp_print_string fmt (Rpn.string_of_error e))
    ( = )

let check = Alcotest.(check (result int error_t))

let test_arithmetic () =
  check "add" (Ok 7) (Rpn.eval "3 4 +");
  check "precedence by order" (Ok 14) (Rpn.eval "3 4 + 2 *");
  check "subtract order" (Ok 1) (Rpn.eval "5 4 -");
  check "extra spaces" (Ok 6) (Rpn.eval "  2   3  * ")

let test_errors () =
  check "empty" (Error Rpn.Empty) (Rpn.eval "   ");
  check "underflow" (Error Rpn.Stack_underflow) (Rpn.eval "1 +");
  check "bad token" (Error (Rpn.Bad_token "x")) (Rpn.eval "1 x +");
  check "leftover" (Error (Rpn.Leftover 2)) (Rpn.eval "1 2")

let () =
  Alcotest.run "rpn"
    [
      ( "eval",
        [
          Alcotest.test_case "arithmetic" `Quick test_arithmetic;
          Alcotest.test_case "errors" `Quick test_errors;
        ] );
    ]
