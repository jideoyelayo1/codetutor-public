let sum n =
  let rec go acc n = if n = 0 then acc else (go [@tailcall]) (acc + n) (n - 1) in
  go 0 n
