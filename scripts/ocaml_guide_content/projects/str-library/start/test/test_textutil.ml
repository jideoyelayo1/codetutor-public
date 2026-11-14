let () =
  assert (Textutil.numbers "a1b22c333" = [ 1; 22; 333 ]);
  assert (Textutil.numbers "none here" = []);
  assert (Textutil.numbers "7" = [ 7 ]);
  assert (Textutil.numbers "12,34;56" = [ 12; 34; 56 ]);
  assert (Textutil.words "  the quick\tbrown\nfox " = [ "the"; "quick"; "brown"; "fox" ]);
  assert (Textutil.words "" = []);
  assert (Textutil.squeeze "  a   b \t c  " = "a b c");
  assert (Textutil.squeeze "single" = "single");
  print_endline "textutil ok"
