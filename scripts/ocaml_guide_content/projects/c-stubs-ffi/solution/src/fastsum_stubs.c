#include <caml/alloc.h>
#include <caml/memory.h>
#include <caml/mlvalues.h>

CAMLprim value ml_sum_ints(value arr) {
  mlsize_t n = Wosize_val(arr);
  long total = 0;
  for (mlsize_t i = 0; i < n; i++) {
    total += Long_val(Field(arr, i));
  }
  return Val_long(total);
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
