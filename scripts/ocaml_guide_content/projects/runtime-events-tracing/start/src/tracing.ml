(* TODO: count the runtime phases triggered by one full major collection.
   Steps: Runtime_events.start (); create a cursor on this process
   (Runtime_events.create_cursor None); build callbacks with
   Runtime_events.Callbacks.create ~runtime_begin:(fun _domain _time _phase -> ...) ();
   run Gc.full_major (); poll once with Runtime_events.read_poll cursor callbacks None;
   free the cursor with Runtime_events.free_cursor; return the count. *)
let count_gc_events () : int = 0
