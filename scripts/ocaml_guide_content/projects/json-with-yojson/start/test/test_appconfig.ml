let is_error = function Error _ -> true | Ok _ -> false

let () =
  (match Appconfig.parse {|{"name": "svc", "port": 8080, "tags": ["a", "b"]}|} with
  | Ok c ->
      assert (c.Appconfig.name = "svc");
      assert (c.Appconfig.port = 8080);
      assert (c.Appconfig.tags = [ "a"; "b" ])
  | Error m -> failwith m);
  assert (is_error (Appconfig.parse {|{"name": "svc", "tags": []}|}));
  assert (is_error (Appconfig.parse {|{"name": "svc", "port": "80", "tags": []}|}));
  assert (is_error (Appconfig.parse {|{"name": 1, "port": 80, "tags": []}|}));
  assert (is_error (Appconfig.parse "{not json"));
  let c = { Appconfig.name = "x"; port = 80; tags = [ "a"; "b" ] } in
  assert (Yojson.Safe.to_string (Appconfig.to_json c) = {|{"name":"x","port":80,"tags":["a","b"]}|});
  (match Appconfig.parse (Yojson.Safe.to_string (Appconfig.to_json c)) with
  | Ok c' -> assert (c' = c)
  | Error m -> failwith m);
  print_endline "appconfig ok"
