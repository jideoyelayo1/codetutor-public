let is_error = function Error _ -> true | Ok _ -> false

let () =
  assert (Calc.calc "1+2*3" = Ok 7);
  assert (Calc.calc "(1+2)*3" = Ok 9);
  assert (Calc.calc "2-3-4" = Ok (-5));
  assert (Calc.calc "-3+5" = Ok 2);
  assert (Calc.calc "--4" = Ok 4);
  assert (Calc.calc "8/2/2" = Ok 2);
  assert (Calc.calc " 2 * ( 3 + 4 ) * 5 " = Ok 70);
  assert (Calc.calc "1/0" = Error "division by zero");
  assert (is_error (Calc.calc "1+"));
  assert (is_error (Calc.calc "(1"));
  assert (is_error (Calc.calc "1 2"));
  assert (is_error (Calc.calc ""));
  assert (is_error (Calc.calc "1 $ 2"));
  print_endline "calc ok"
