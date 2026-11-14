let fails s = match Calc_gen.calc s with _ -> false | exception _ -> true

let () =
  assert (Calc_gen.calc "1+2*3" = 7);
  assert (Calc_gen.calc "2*3+4" = 10);
  assert (Calc_gen.calc "2-3-4" = -5);
  assert (Calc_gen.calc "-(2+3)*2" = -10);
  assert (Calc_gen.calc " ( 1 + 2 ) * 3 " = 9);
  assert (Calc_gen.calc "10-2*3-1" = 3);
  assert (fails "1 +");
  assert (fails "1 $ 2");
  print_endline "calc_gen ok"
