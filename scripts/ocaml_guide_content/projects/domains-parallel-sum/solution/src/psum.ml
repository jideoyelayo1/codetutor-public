let sum ~domains a =
  if domains < 1 then invalid_arg "Psum.sum: domains must be at least 1";
  let n = Array.length a in
  let chunk lo hi =
    let total = ref 0 in
    for i = lo to hi - 1 do
      total := !total + a.(i)
    done;
    !total
  in
  if n = 0 then 0
  else
    let size = (n + domains - 1) / domains in
    List.init domains (fun d ->
        let lo = min n (d * size) and hi = min n ((d + 1) * size) in
        Domain.spawn (fun () -> chunk lo hi))
    |> List.map Domain.join
    |> List.fold_left ( + ) 0
