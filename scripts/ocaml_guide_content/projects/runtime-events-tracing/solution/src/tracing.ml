let count_gc_events () =
  Runtime_events.start ();
  let cursor = Runtime_events.create_cursor None in
  let count = ref 0 in
  let callbacks =
    Runtime_events.Callbacks.create
      ~runtime_begin:(fun _domain _timestamp _phase -> incr count)
      ()
  in
  Gc.full_major ();
  ignore (Runtime_events.read_poll cursor callbacks None);
  Runtime_events.free_cursor cursor;
  !count
