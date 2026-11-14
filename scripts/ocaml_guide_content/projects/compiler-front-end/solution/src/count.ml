let count_lets source =
  let structure = Parse.implementation (Lexing.from_string source) in
  List.length
    (List.filter
       (fun item -> match item.Parsetree.pstr_desc with Parsetree.Pstr_value _ -> true | _ -> false)
       structure)
