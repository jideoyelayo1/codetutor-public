type token = TNum of int | TOp of char | TLParen | TRParen
type expr = Num of int | Neg of expr | Bin of char * expr * expr

let tokenize s =
  let n = String.length s in
  let is_digit c = c >= '0' && c <= '9' in
  let rec go i acc =
    if i >= n then Ok (List.rev acc)
    else
      match s.[i] with
      | ' ' -> go (i + 1) acc
      | '0' .. '9' ->
          let j = ref i in
          while !j < n && is_digit s.[!j] do
            incr j
          done;
          go !j (TNum (int_of_string (String.sub s i (!j - i))) :: acc)
      | ('+' | '-' | '*' | '/') as c -> go (i + 1) (TOp c :: acc)
      | '(' -> go (i + 1) (TLParen :: acc)
      | ')' -> go (i + 1) (TRParen :: acc)
      | c -> Error (Printf.sprintf "unexpected character %C" c)
  in
  go 0 []

let parse tokens : (expr, string) result =
  let ( let* ) = Result.bind in
  let rec expr ts =
    let* lhs, ts = term ts in
    loop_expr lhs ts
  and loop_expr lhs = function
    | TOp (('+' | '-') as op) :: ts ->
        let* rhs, ts = term ts in
        loop_expr (Bin (op, lhs, rhs)) ts
    | ts -> Ok (lhs, ts)
  and term ts =
    let* lhs, ts = unary ts in
    loop_term lhs ts
  and loop_term lhs = function
    | TOp (('*' | '/') as op) :: ts ->
        let* rhs, ts = unary ts in
        loop_term (Bin (op, lhs, rhs)) ts
    | ts -> Ok (lhs, ts)
  and unary = function
    | TOp '-' :: ts ->
        let* e, ts = unary ts in
        Ok (Neg e, ts)
    | ts -> atom ts
  and atom = function
    | TNum n :: ts -> Ok (Num n, ts)
    | TLParen :: ts -> (
        let* e, ts = expr ts in
        match ts with
        | TRParen :: ts -> Ok (e, ts)
        | _ -> Error "expected )")
    | _ -> Error "expected a number or ("
  in
  let* e, rest = expr tokens in
  if rest = [] then Ok e else Error "unexpected trailing input"

let rec eval = function
  | Num n -> Ok n
  | Neg e -> Result.map (fun n -> -n) (eval e)
  | Bin (op, a, b) ->
      Result.bind (eval a) (fun x ->
          Result.bind (eval b) (fun y ->
              match op with
              | '+' -> Ok (x + y)
              | '-' -> Ok (x - y)
              | '*' -> Ok (x * y)
              | '/' -> if y = 0 then Error "division by zero" else Ok (x / y)
              | _ -> Error "bad operator"))

let calc s =
  Result.bind (tokenize s) (fun tokens -> Result.bind (parse tokens) eval)
