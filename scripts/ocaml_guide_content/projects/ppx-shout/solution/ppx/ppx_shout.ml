open Ppxlib

let expand ~ctxt s =
  let loc = Expansion_context.Extension.extension_point_loc ctxt in
  Ast_builder.Default.estring ~loc (String.uppercase_ascii s)

let extension =
  Extension.V3.declare "shout" Extension.Context.expression
    Ast_pattern.(single_expr_payload (estring __))
    expand

let () = Driver.register_transformation "shout" ~extensions:[ extension ]
