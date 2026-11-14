#include <caml/alloc.h>
#include <caml/memory.h>
#include <caml/mlvalues.h>

/* TODO: add up every element of the OCaml int array [arr].
   Use Wosize_val(arr) for the length, Field(arr, i) for an element,
   Long_val(...) to untag it and Val_long(...) to tag the result. */
CAMLprim value ml_sum_ints(value arr) {
  (void)arr;
  return Val_long(0);
}

/* [range n] is [|0; 1; ...; n-1|]. Storing immediate ints into a freshly
   allocated block needs no GC roots. */
CAMLprim value ml_range(value n_val) {
  long n = Long_val(n_val);
  if (n <= 0) return Atom(0);
  value result = caml_alloc(n, 0);
  for (long i = 0; i < n; i++) Field(result, i) = Val_long(i);
  return result;
}
