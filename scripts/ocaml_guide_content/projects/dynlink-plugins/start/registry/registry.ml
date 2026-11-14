(* The interface shared by the host and every plug-in. *)
let plugins : (string * (int -> int)) list ref = ref []
let register name f = plugins := (name, f) :: !plugins
