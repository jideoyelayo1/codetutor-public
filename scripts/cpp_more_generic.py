"""Additional original C++ units and drills for stages 05-06."""
from cpp_lessons import unit, program
from cpp_drills import drill, main_program

S5 = '05 Generic and compile-time programming'
S6 = '06 Collections, algorithms, and ranges'


def body(text):
    """Indent a block of statements for main()."""
    return '\n'.join('    ' + line for line in text.strip('\n').split('\n'))


def code(text, headers='', decl=''):
    return main_program(body(text), ('iostream ' + headers).strip(), decl.strip('\n'))


def out(lesson, title, text, headers, correct, wrong, why, decl='', std=None, kind='Predict output'):
    drill(lesson, kind, title, code(text, headers, decl), 'What does this program print?', correct, wrong, why, standard=std)


def rej(lesson, title, text, headers, diag, correct, wrong, why, decl='', std=None):
    drill(lesson, 'Compiles?', title, code(text, headers, decl), 'Does this program compile?', correct, wrong, why,
          check='reject', diagnostic=diag, standard=std)


def ok(lesson, title, text, headers, correct, wrong, why, decl='', std=None):
    drill(lesson, 'Compiles?', title, code(text, headers, decl), 'Does this program compile?', correct, wrong, why,
          check='compiles', standard=std)


def san(lesson, check, title, text, headers, question, correct, wrong, why, decl='', std=None):
    drill(lesson, 'Undefined behavior', title, code(text, headers, decl), question, correct, wrong, why, check=check, standard=std)


def think(lesson, kind, title, question, correct, wrong, why, complexity=None):
    drill(lesson, kind, title, '', question, correct, wrong, why, check='reasoning', complexity=complexity)


# New stage-05 units
unit(S5, 'tag-dispatch-traits', 'Type traits select an implementation through tag dispatch', 14,
     "A type trait is a compile-time query or transformation over types. iterator_traits exposes an iterator category tag, and passing an object of that tag type to an overloaded helper lets ordinary overload resolution choose an implementation before the program runs.|The iterator tags form an inheritance chain: random_access derives from bidirectional, which derives from forward, which derives from input. A helper overload taking a base tag therefore accepts every stronger category, and an exact-match overload for a stronger tag wins when it exists.|Tag dispatch selects code, it does not check semantics. A user iterator that advertises random_access_iterator_tag without constant-time jumps silently receives the wrong algorithm; the tag is a promise the type author must keep.",
     program('iterator list vector', body(r'''
std::vector<int> v{1, 2, 3};
std::list<int> l{1, 2, 3};
std::cout << steps(v.begin()) << " " << steps(l.begin()) << "\n";'''), r'''template<class It> int stepsImpl(It, std::random_access_iterator_tag) { return 1; }
template<class It> int stepsImpl(It, std::input_iterator_tag) { return 2; }
template<class It> int steps(It it) {
    return stepsImpl(it, typename std::iterator_traits<It>::iterator_category{});
}
'''), '1 2\n',
     ('Add a dedicated bidirectional overload that returns 3 and observe which helper the list iterator now selects.',
      'template<class It> int stepsImpl(It, std::input_iterator_tag) { return 2; }',
      'template<class It> int stepsImpl(It, std::input_iterator_tag) { return 2; }\ntemplate<class It> int stepsImpl(It, std::bidirectional_iterator_tag) { return 3; }',
      '1 3\n', 'The list tag is bidirectional_iterator_tag. An exact match now exists, so the derived-to-base conversion to input_iterator_tag is no longer the best candidate. The vector call still matches random access exactly.'),
     'Why does a list iterator reach the input_iterator_tag overload when only random-access and input overloads exist?',
     'bidirectional_iterator_tag derives (through forward) from input_iterator_tag, so the base conversion is viable',
     ['Overload resolution picks the last declared overload', 'list iterators report input_iterator_tag'],
     'Tag types are ordinary classes. A derived-to-base conversion makes the input overload viable, while the random-access overload is not.', 'iterator.traits')

unit(S5, 'if-constexpr-branches', 'if constexpr discards the branch a type cannot use', 17,
     "if constexpr evaluates its condition as a constant expression. Inside a template, the branch not taken is a discarded statement and is not instantiated for that specialization, so it may contain operations the current type does not support.|This replaces many tag-dispatch and enable_if patterns with straight-line code. Each branch may return a different type when the function uses deduced return type, because only the selected return statements participate in deduction.|Outside a template the discarded branch is still fully checked, and even inside a template it must be syntactically valid and not ill-formed for every possible type. A plain if with a constant condition instantiates both branches.",
     program('string type_traits', body(r'''
std::cout << describe(21) << " " << describe("hi") << "\n";'''), r'''template<class T> std::string describe(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        return "int:" + std::to_string(value * 2);
    } else {
        return "text:" + std::string(value);
    }
}
'''), 'int:42 text:hi\n',
     ('Describe a long value instead of the int.', 'describe(21)', 'describe(5L)', 'int:10 text:hi\n',
      'long is integral, so the first branch is instantiated for T=long. The character-array call still instantiates only the else branch, where value*2 would be ill-formed.'),
     'For describe("hi"), why is value * 2 not an error?',
     'The integral branch is a discarded statement and is not instantiated for T = const char[3]',
     ['Arrays support multiplication by an integer', 'if constexpr converts errors into runtime exceptions'],
     'Inside a template, a discarded constexpr branch is not instantiated for that specialization.', 'stmt.if')

unit(S5, 'auto-nttp', 'Non-type template parameters can deduce their type', 17,
     "A non-type template parameter is a compile-time value that becomes part of the type. Since C++17, template<auto N> deduces the parameter type from the argument, so Constant<5> and Constant<'x'> are both valid and carry different value types.|C++20 widened the permitted parameter types: floating-point values and structural class types (all bases and members public and themselves structural) can be template arguments. Two arguments name the same specialization only when their values are template-argument-equivalent.|Each distinct value creates a distinct type, which can multiply instantiations and code size. Pointer arguments must refer to objects with static storage duration; a string literal itself cannot be a template argument.",
     program('type_traits', body(r'''
std::cout << Constant<5>::value << " " << Constant<'x'>::value << " ";
std::cout << std::is_same_v<decltype(Constant<5u>::value), const unsigned> << "\n";'''),
             r'''template<auto N> struct Constant { static constexpr auto value = N; };
'''), '5 x 1\n',
     ('Use a constant expression rather than a literal for the first argument.', 'Constant<5>::value', 'Constant<40 + 2>::value', '42 x 1\n',
      'Any converted constant expression of a permitted type works. The argument is evaluated during translation and its int type is deduced.'),
     'Are Constant<5> and Constant<5u> the same type?', 'No; the deduced parameter types differ (int versus unsigned)',
     ['Yes, because the values are equal', 'Only on platforms where int and unsigned have the same width'],
     'With auto, the argument type is part of the template argument, so equal numeric values of different types name different specializations.', 'temp.param')

unit(S5, 'template-template-params', 'Template template parameters accept a template, not a type', 14,
     "A template template parameter lets a class template receive another template, such as std::vector, and apply it to types of its own choosing. Bag<std::vector> passes the template; Bag<std::vector<int>> would pass a type and does not match.|The parameter declares the shape it expects. Standard containers have a defaulted allocator parameter, so a portable declaration either lists both parameters or uses a variadic pack. C++17 relaxed matching lets a parameter with fewer parameters accept a template with defaulted extras, but older compilers needed a flag.|Do not use this feature when a type parameter would do. Accepting a fully formed container type is usually simpler and lets callers supply allocators and comparators directly.",
     program('list memory vector', body(r'''
Bag<std::vector> bag;
bag.add(3);
bag.add(4);
std::cout << bag.items.size() << " " << bag.items.back() << "\n";'''), r'''template<template<class, class> class Container>
struct Bag {
    Container<int, std::allocator<int>> items;
    void add(int v) { items.push_back(v); }
};
'''), '2 4\n',
     ('Store the items in a std::list instead.', 'Bag<std::vector> bag;', 'Bag<std::list> bag;', '2 4\n',
      'std::list also takes an element type and an allocator, so it matches the declared template shape. Bag uses only push_back, size and back, which list supports.'),
     'Which argument matches template<template<class, class> class Container>?', 'std::vector',
     ['std::vector<int>', 'std::vector<int>::iterator'],
     'A template template parameter requires a template name, not a specialization or another type.', 'temp.arg.template')

unit(S5, 'variable-templates', 'Variable templates name a family of constants', 14,
     "A variable template declares a variable parameterized by types or values, such as pi<T> or is_small<T>. Each specialization is a separate variable, typically constexpr, and the standard _v traits are variable templates over the class-template traits.|Variable templates can be partially and explicitly specialized, which makes recursive compile-time definitions such as pointer depth concise. They are instantiated only when used.|A non-const variable template creates one mutable global per type, with the usual initialization-order and data-race concerns. Converting a long double initializer to int truncates; the template does not choose a safe rounding policy.",
     program('', body(r'''
std::cout << pi<int> << " " << is_small<short> << is_small<long> << "\n";'''),
             r'''template<class T> constexpr T pi = T(3.1415926535897932385L);
template<class T> constexpr bool is_small = sizeof(T) <= 2;
'''), '3 10\n',
     ('Test char instead of long.', 'is_small<long>', 'is_small<char>', '3 11\n',
      'sizeof(char) is 1 by definition, so is_small<char> is true. sizeof(short) is at least 2 bytes and is 2 on this target.'),
     'What does pi<int> evaluate to?', '3, because the long double value is converted to int by truncation',
     ['4, because the conversion rounds to nearest', 'It does not compile for integral types'],
     'T(value) performs a functional cast; floating-to-integral conversion truncates toward zero.', 'temp.pre')

unit(S5, 'dependent-base-lookup', 'Names from a dependent base need this-> or qualification', 14,
     "Templates are checked in two phases. Non-dependent names are looked up when the template is defined; dependent names are resolved at instantiation. A base class that depends on a template parameter is not searched by unqualified lookup at definition time, because its members are unknown until instantiation.|Writing this->size() or Base<T>::size() makes the name dependent, deferring lookup to the instantiated base. Without it, unqualified lookup may silently find an unrelated global function or fail with an undeclared-identifier error.|Argument-dependent lookup at the point of instantiation can still find functions declared after the template, but only through associated namespaces of class-type arguments. Fundamental types have none, so a later overload for int is not found.",
     program('', body(r'''
std::cout << Derived<int>{}.report() << "\n";'''), r'''int size() { return 99; }
template<class T> struct Base { int size() const { return 3; } };
template<class T> struct Derived : Base<T> {
    int report() const { return this->size(); }
};
'''), '3\n',
     ('Remove this-> and observe which size the template binds.', 'return this->size();', 'return size();', '99\n',
      'size() is now a non-dependent name. Lookup at the definition finds the global size and ignores the dependent base, so report returns 99.'),
     'Why is the base member found only with this->?', 'this-> makes the name dependent, so lookup happens in the instantiated base',
     ['this-> forces virtual dispatch', 'Unqualified lookup searches dependent bases only in C++20'],
     'Unqualified lookup does not search a dependent base class at the template definition.', 'temp.dep')

unit(S5, 'forwarding-vs-rvalue', 'T&& is a forwarding reference only when T is deduced', 14,
     "In a function template, a parameter of the form T&& where T is deduced from the call is a forwarding reference. An lvalue argument deduces T as an lvalue reference and reference collapsing yields T&; an rvalue deduces a non-reference T.|In a member of a class template, T is already fixed by the class, so void take(T&&) is an ordinary rvalue reference parameter and rejects lvalues. const T&& and std::vector<T>&& are not forwarding references either.|A greedy forwarding overload often beats an overload taking const X& for non-const lvalues, because it deduces an exact match. Constrain forwarding constructors or overloads rather than assuming the const reference version is preferred.",
     program('type_traits', body(r'''
int n = 1;
Box<int> box;
box.take(5);
std::cout << kind(n) << " " << kind(2) << "\n";'''), r'''template<class T> const char* kind(T&&) {
    return std::is_lvalue_reference<T>::value ? "lvalue" : "rvalue";
}
template<class T> struct Box {
    void take(T&&) {}
};
'''), 'lvalue rvalue\n',
     ('Pass n as an xvalue.', 'kind(n)', 'kind(std::move(n))', 'rvalue rvalue\n',
      'std::move produces an xvalue, so deduction yields a non-reference T and the trait reports an rvalue.'),
     'Can Box<int>::take accept an int lvalue?', 'No; T is fixed by the class, so T&& is an ordinary rvalue reference',
     ['Yes; every T&& is a forwarding reference', 'Yes, but only for const lvalues'],
     'Forwarding reference deduction requires T to be a template parameter of the function being called.', 'temp.deduct.call')

unit(S5, 'concept-subsumption', 'Subsumption picks the more constrained overload', 20,
     "When two constrained candidates are otherwise equally good, the one whose constraints subsume the other wins. Constraints are normalized into conjunctions and disjunctions of atomic constraints, and subsumption compares those atoms.|Whole is defined as Number<T> && is_integral_v<T>, so it contains Number as a conjunct and is more constrained. For an int argument both pick overloads are viable and the Whole overload is chosen; for a double only Number is satisfied.|Atomic constraints are identical only if they come from the same expression in the source, normally via the same concept. Repeating std::is_integral_v<T> textually in two requires-clauses does not create subsumption and yields an ambiguity.",
     program('concepts type_traits', body(r'''
std::cout << pick(2.5) << " " << pick(7) << "\n";'''), r'''template<class T> concept Number = std::is_arithmetic_v<T>;
template<class T> concept Whole = Number<T> && std::is_integral_v<T>;
const char* pick(Number auto) { return "number"; }
const char* pick(Whole auto) { return "whole"; }
'''), 'number whole\n',
     ('Pass a floating literal in the second call.', 'pick(7)', 'pick(7.0)', 'number number\n',
      'double satisfies Number but not Whole, so only the first overload is viable.'),
     'Why is pick(7) not ambiguous?', 'Whole subsumes Number because Whole is defined as a conjunction containing Number',
     ['The later declaration always wins', 'Integral types always prefer the overload declared with auto'],
     'Normalized constraints compare atomic constraints that come from the same concept definition.', 'temp.constr.order')

unit(S5, 'index-sequences', 'index_sequence turns a pack of indices into code', 14,
     "std::integer_sequence<T, I...> carries a compile-time pack of integers in its type. make_index_sequence<N> produces indices 0..N-1 and index_sequence_for<Ts...> produces one index per type.|A helper deduces the pack from the sequence argument and expands an expression such as std::get<I>(t) for each index. In C++14 a braced array initializer sequences the expansions left to right; C++17 fold expressions express the same idea more directly.|The sequence object is empty; all the information lives in its type. Large N creates large instantiations and slow builds, and negative lengths are rejected.",
     program('cstddef tuple utility', body(r'''
std::cout << sumAll(std::make_tuple(1, 2, 3)) << " " << std::make_index_sequence<4>::size() << "\n";'''),
             r'''template<class Tuple, std::size_t... I>
int sumImpl(const Tuple& t, std::index_sequence<I...>) {
    int total = 0;
    int expand[] = {0, (total += std::get<I>(t), 0)...};
    (void)expand;
    return total;
}
template<class... T> int sumAll(const std::tuple<T...>& t) {
    return sumImpl(t, std::index_sequence_for<T...>{});
}
'''), '6 4\n',
     ('Sum a two-element tuple instead.', 'std::make_tuple(1, 2, 3)', 'std::make_tuple(10, 20)', '30 4\n',
      'index_sequence_for<int, int> is index_sequence<0, 1>, so two get expansions are generated.'),
     'Where are the indices stored in std::index_sequence<0, 1, 2>?', 'In the type itself; the object carries no data',
     ['In a heap-allocated array', 'In three int data members'],
     'integer_sequence is an empty class whose template arguments encode the values.', 'intseq')

unit(S5, 'typelists', 'A typelist is a pack you can query and transform', 17,
     "A typelist is an empty class template holding a pack of types. Metafunctions are partial specializations that pattern-match the pack and expose a result as a static value or nested type alias.|Fold expressions make queries such as Contains a single line. Transformations such as front, push or map produce a new TypeList type instead of mutating anything.|Every intermediate list is a distinct instantiation. Applying a metafunction to a list shape it does not handle, such as Front of an empty list, produces an incomplete-type error rather than a clear message unless you add a static_assert.",
     program('cstddef type_traits', body(r'''
std::cout << Length<Numbers>::value << " " << Contains<Numbers, long>::value << Contains<Numbers, char>::value << "\n";'''),
             r'''template<class... T> struct TypeList {};
template<class List> struct Length;
template<class... T> struct Length<TypeList<T...>> {
    static constexpr std::size_t value = sizeof...(T);
};
template<class List, class U> struct Contains;
template<class... T, class U> struct Contains<TypeList<T...>, U> {
    static constexpr bool value = (std::is_same_v<T, U> || ...);
};
using Numbers = TypeList<int, long, double>;
'''), '3 10\n',
     ('Ask whether double is in the list.', 'Contains<Numbers, char>', 'Contains<Numbers, double>', '3 11\n',
      'double is the third element, so one is_same_v term is true and the disjunction is true.'),
     'What does (std::is_same_v<T, U> || ...) yield for an empty TypeList<>?', 'false, the identity of a unary || fold',
     ['true', 'It fails to compile'], 'A unary fold over an empty pack is permitted for &&, || and the comma operator.', 'temp.variadic')

unit(S5, 'constexpr-allocation', 'C++20 constant evaluation can allocate transiently', 20,
     "Since C++20, constant evaluation may call new and delete, and std::vector and std::string have constexpr members. A constexpr function can build a vector, compute with it and return a scalar result during translation.|The allocation must be released before the constant evaluation ends. A transient vector that is destroyed inside the function is fine; a constexpr variable whose value still owns heap memory is ill-formed.|The same function remains callable at runtime with dynamic allocation. Compilers bound constant-evaluation steps, so very large compile-time computations can fail with a limit rather than a logic error.",
     program('vector', body(r'''
constexpr int result = sumSquares(4);
static_assert(result == 30);
std::cout << result << "\n";'''), r'''constexpr int sumSquares(int n) {
    std::vector<int> squares;
    for (int i = 1; i <= n; ++i) squares.push_back(i * i);
    int total = 0;
    for (int x : squares) total += x;
    return total;
}
'''), '30\n',
     ('Compute the sum for five squares and update the assertion.', 'sumSquares(4);\n    static_assert(result == 30', 'sumSquares(5);\n    static_assert(result == 55',
      '55\n', '1+4+9+16+25 is 55. The vector is created and destroyed inside one constant evaluation.'),
     'Can a constexpr std::vector<int> variable keep its heap elements after constant evaluation?',
     'No; every allocation must be deallocated within the same constant evaluation',
     ['Yes, the compiler stores them in read-only data', 'Yes, but only for fewer than 16 elements'],
     'C++20 permits transient constexpr allocation only.', 'expr.const')

# New stage-06 units
unit(S6, 'list-splice', 'Node containers move elements without invalidating them', 14,
     "std::list and std::forward_list store each element in its own node. splice relinks nodes from one list into another in constant time for a whole list or single element, without copying or moving the element values.|Iterators, pointers and references to spliced elements remain valid; they now refer into the destination list. deque differs: insertion at either end invalidates iterators but keeps references to existing elements valid, while vector reallocation invalidates all three.|Splicing a range between different lists is linear because the size must be recounted. Node containers trade locality and per-node allocation for this stability, so they are slower to traverse than vector.",
     program('list', body(r'''
std::list<int> a{1, 2, 3};
std::list<int> b{10, 20};
auto it = b.begin();
a.splice(a.end(), b);
std::cout << *it << " " << a.size() << " " << b.size() << "\n";''')), '10 5 0\n',
     ('Splice only the node that it refers to, placing it at the front of a.', 'a.splice(a.end(), b);', 'a.splice(a.begin(), b, it);', '10 4 1\n',
      'The single-element overload relinks one node. it still refers to the 10 node, now first in a, and b keeps 20.'),
     'After splicing all of b into a, what happens to an iterator into b?', 'It stays valid and now refers to an element of a',
     ['It becomes invalid', 'It refers to b.end()'], 'splice moves nodes, not values, so iterators follow their elements.', 'list.ops')

unit(S6, 'hash-load-factor', 'Hashed containers trade buckets for load factor', 14,
     "An unordered container stores elements in buckets chosen by the hash. load_factor is size divided by bucket_count; when an insertion would exceed max_load_factor the container rehashes into more buckets.|reserve(n) prepares enough buckets for n elements without further rehashing. A custom hash must agree with equality: equal keys must produce equal hashes, and good spread keeps chains short.|Rehashing invalidates iterators but not references or pointers to elements. Never print or test unordered iteration order; it depends on the hash, the bucket count and the implementation.",
     program('cstddef functional unordered_set', body(r'''
std::unordered_set<Point, PointHash> points;
points.reserve(100);
points.insert(Point{1, 2});
points.insert(Point{1, 2});
points.insert(Point{2, 1});
std::cout << points.size() << " " << (points.bucket_count() >= 100) << " " << (points.load_factor() <= points.max_load_factor()) << "\n";'''),
             r'''struct Point {
    int x, y;
    bool operator==(const Point& other) const { return x == other.x && y == other.y; }
};
struct PointHash {
    std::size_t operator()(const Point& p) const noexcept {
        return std::hash<int>{}(p.x) * 31u + std::hash<int>{}(p.y);
    }
};
'''), '2 1 1\n',
     ('Insert a third distinct point.', 'points.insert(Point{2, 1});', 'points.insert(Point{2, 1});\n    points.insert(Point{3, 4});', '3 1 1\n',
      'The duplicate {1, 2} was rejected by equality, so three distinct points remain. reserve already supplied enough buckets.'),
     'Which property must a custom hash satisfy?', 'Keys that compare equal must produce equal hash values',
     ['Distinct keys must produce distinct hash values', 'The hash must be smaller than bucket_count'],
     'Collisions are allowed; inconsistency with equality breaks lookup.', 'unord.req')

unit(S6, 'heterogeneous-lookup', 'Transparent comparators avoid temporary keys', 20,
     "By default, map<string, V>::find takes const string&, so looking up a string_view or const char* constructs a temporary string. A transparent comparator such as std::less<> declares is_transparent and enables find, count, contains and lower_bound templates that accept any comparable type.|C++20 extends this to unordered containers: both the hash and the key-equal type must declare is_transparent, for example a string_view hash with std::equal_to<>.|The comparator must order the other type consistently with the key ordering. Transparent lookup does not apply to operator[] or insert, which still need a key_type.",
     program('functional map string string_view unordered_map', body(r'''
std::map<std::string, int, std::less<>> ordered{{"apple", 1}};
std::unordered_map<std::string, int, StringHash, std::equal_to<>> hashed{{"pear", 2}};
std::string_view key = "apple";
std::cout << ordered.find(key)->second << " " << hashed.find(std::string_view("pear"))->second << "\n";'''),
             r'''struct StringHash {
    using is_transparent = void;
    std::size_t operator()(std::string_view s) const noexcept { return std::hash<std::string_view>{}(s); }
};
'''), '1 2\n',
     ('Count a missing key in the hashed container.', 'hashed.find(std::string_view("pear"))->second', 'hashed.count(std::string_view("plum"))', '1 0\n',
      'count also has a transparent overload; plum is absent, so it returns zero without building a string.'),
     'What enables map::find(string_view) on a map<string, int, std::less<>>?', 'std::less<> is transparent, which enables the template find overload',
     ['string_view converts implicitly to string', 'All C++20 maps accept any key type'],
     'The heterogeneous overloads exist only when the comparator declares is_transparent.', 'associative.reqmts')

unit(S6, 'node-handles', 'Node handles move elements between associative containers', 17,
     "extract removes an element from a map or set and returns a node handle that owns it. The key of an extracted map node can be modified, and insert(std::move(node)) relinks it into a compatible container without copying or reallocating.|merge transfers every element whose key is not already present in the destination. Elements with conflicting keys stay in the source.|If inserting a node fails because the key exists, the returned insert_return_type holds the node; discarding that result destroys the element. A moved-from or empty node handle must not be dereferenced.",
     program('map string', body(r'''
std::map<int, std::string> a{{1, "one"}, {2, "two"}};
std::map<int, std::string> b{{2, "deux"}, {3, "trois"}};
auto node = a.extract(1);
node.key() = 4;
b.insert(std::move(node));
a.merge(b);
std::cout << a.size() << " " << b.size() << " " << b.begin()->second << "\n";''')), '3 1 deux\n',
     ('Relabel the extracted node with a key that b already contains.', 'node.key() = 4;', 'node.key() = 3;', '2 1 deux\n',
      'Insertion fails because 3 exists, and the discarded insert_return_type destroys the node. merge then moves only key 3 into a.'),
     'During a.merge(b), what happens to an element of b whose key already exists in a?', 'It stays in b',
     ['It overwrites the element in a', 'merge throws'], 'merge never replaces existing keys; it only transfers non-conflicting nodes.', 'container.node')

unit(S6, 'range-projections', 'Range algorithms accept a projection', 20,
     "C++20 range algorithms take an optional projection applied to each element before the comparator or predicate sees it. Sorting by &Employee::age uses std::invoke, so pointers to data members and to member functions work directly.|The comparator slot comes first; {} selects its default, std::ranges::less. find takes a value followed by a projection, and the projected value is compared with ==.|A projection is called many times and must not mutate or depend on changing state. The algorithms return results such as iterators or dangling markers, never a copy of the sorted range.",
     program('algorithm functional string vector', body(r'''
std::vector<Employee> staff{{"Ada", 36}, {"Bo", 25}, {"Cy", 41}};
std::ranges::sort(staff, {}, &Employee::age);
for (const auto& e : staff) std::cout << e.name << " ";
auto it = std::ranges::find(staff, std::string("Cy"), &Employee::name);
std::cout << it->age << "\n";'''), r'''struct Employee {
    std::string name;
    int age;
};
'''), 'Bo Ada Cy 41\n',
     ('Sort by age in descending order.', 'std::ranges::sort(staff, {}, &Employee::age)', 'std::ranges::sort(staff, std::ranges::greater{}, &Employee::age)', 'Cy Ada Bo 41\n',
      'The comparator changes while the projection still extracts age. find is unaffected because it searches for the name.'),
     'In std::ranges::sort(v, {}, &Employee::age), what does {} mean?', 'Use the default comparator, std::ranges::less',
     ['Sort without a comparator in unspecified order', 'An empty projection'], 'The second argument is the comparator; value-initializing it selects ranges::less.', 'alg.sort')

unit(S6, 'custom-iterator', 'A custom iterator must model the concept it claims', 20,
     "To make a type usable in range-for and the range algorithms, give it begin and end returning an iterator. For std::forward_iterator the iterator needs value_type, difference_type, dereference, prefix and postfix increment, default construction and equality.|A static_assert on the concept documents and verifies the intended category. Defaulted operator== supplies equality, and the iterator may return values by value as long as the range does not promise references.|Satisfying a concept checks syntax, not meaning. A forward iterator must be multipass: copies advance independently and equal iterators dereference to the same value. Breaking that law compiles but makes algorithms wrong.",
     program('cstddef iterator', body(r'''
for (int x : Countdown{3}) std::cout << x << " ";
std::cout << std::ranges::distance(Countdown{5}) << "\n";'''), r'''struct Countdown {
    struct iterator {
        using value_type = int;
        using difference_type = std::ptrdiff_t;
        int current = 0;
        int operator*() const { return current; }
        iterator& operator++() { --current; return *this; }
        iterator operator++(int) { iterator copy = *this; --current; return copy; }
        bool operator==(const iterator&) const = default;
    };
    int start;
    iterator begin() const { return iterator{start}; }
    iterator end() const { return iterator{0}; }
};
static_assert(std::forward_iterator<Countdown::iterator>);
'''), '3 2 1 5\n',
     ('Count down from four.', 'Countdown{3}', 'Countdown{4}', '4 3 2 1 5\n',
      'begin starts at four and end compares equal at zero. distance walks the separate five-element range.'),
     'What does static_assert(std::forward_iterator<It>) verify?', 'The required operations and associated types exist with the right forms',
     ['That the iterator is genuinely multipass at runtime', 'That traversal is constant time'],
     "Concepts check syntactic requirements; semantic requirements remain the author's responsibility.", 'iterator.concept.forward')

unit(S6, 'binary-search-bounds', 'lower_bound and upper_bound bracket equal elements', 14,
     "lower_bound returns the first position whose element is not less than the value; upper_bound returns the first position whose element is greater. Together they bracket the run of equivalent elements, which equal_range returns as a pair.|These algorithms require the range to be partitioned with respect to the value under the same comparator, which a sorted range satisfies. They use O(log n) comparisons.|On non-random-access iterators the comparisons stay logarithmic but stepping is linear. Use set::lower_bound rather than std::lower_bound on set iterators. An unsorted input violates the precondition and gives meaningless results.",
     program('algorithm vector', body(r'''
std::vector<int> v{1, 3, 3, 3, 7};
const int key = 3;
auto lo = std::lower_bound(v.begin(), v.end(), key);
auto hi = std::upper_bound(v.begin(), v.end(), key);
auto range = std::equal_range(v.begin(), v.end(), key);
std::cout << (lo - v.begin()) << " " << (hi - v.begin()) << " " << (range.second - range.first) << "\n";''')), '1 4 3\n',
     ('Search for a value that is absent.', 'const int key = 3;', 'const int key = 4;', '4 4 0\n',
      'Both bounds land at the insertion point before 7, so the equal range is empty.'),
     'For an absent value, what do lower_bound and upper_bound return?', 'The same position: where the value could be inserted keeping order',
     ['end() for both', 'lower_bound returns begin()'], 'Neither bound requires the value to be present; they describe a partition point.', 'alg.binary.search')

unit(S6, 'selection-algorithms', 'Sort only as much as the question needs', 14,
     "partial_sort places the k smallest elements in sorted order at the front in O(n log k). nth_element places the element that would be at position k after a full sort there, with smaller-or-equal elements before it and greater-or-equal after, in average linear time.|stable_sort preserves the relative order of equivalent elements, at the cost of extra memory or an O(n log^2 n) fallback. sort gives no stability guarantee.|After nth_element, neither side is sorted. After partial_sort, the tail is in unspecified order. Read only the guarantees the algorithm makes.",
     program('algorithm vector', body(r'''
std::vector<int> v{9, 4, 7, 1, 8, 2};
std::vector<int> w = v;
std::partial_sort(v.begin(), v.begin() + 3, v.end());
for (int i = 0; i < 3; ++i) std::cout << v[i] << " ";
std::nth_element(w.begin(), w.begin() + 2, w.end());
std::cout << "| " << w[2] << "\n";''')), '1 2 4 | 4\n',
     ('Select the element at index three instead.', [('w.begin() + 2,', 'w.begin() + 3,'), ('w[2]', 'w[3]')], None, '1 2 4 | 7\n',
      'The sorted sequence is 1 2 4 7 8 9, so index three holds 7. nth_element places exactly that value there.'),
     'After nth_element(first, first + k, last), which statement is guaranteed?', 'Elements before position k are not greater than the element at k',
     ['The first k elements are sorted', 'The whole range is sorted'], 'nth_element only guarantees the partition around the selected element.', 'alg.nth.element')

unit(S6, 'searchers', 'Searcher objects precompute a pattern for repeated search', 17,
     "C++17 std::search accepts a searcher object. boyer_moore_searcher and boyer_moore_horspool_searcher preprocess the pattern once, then skip ahead through the text using mismatch tables, often examining fewer than n characters.|A searcher is also callable directly and returns a pair of iterators for the match. default_searcher wraps the ordinary algorithm.|Boyer-Moore needs random-access iterators and builds tables proportional to the pattern and alphabet; for very short patterns or text the setup can cost more than it saves. Measure before switching.",
     program('algorithm functional string', body(r'''
std::string text = "the quick brown fox";
std::string needle = "brown";
auto it = std::search(text.begin(), text.end(), std::boyer_moore_searcher(needle.begin(), needle.end()));
std::cout << (it - text.begin()) << "\n";''')), '10\n',
     ('Search for fox instead.', 'needle = "brown"', 'needle = "fox"', '16\n',
      'fox starts at offset 16. The searcher is rebuilt for the new pattern.'),
     'What does boyer_moore_searcher precompute?', 'Skip tables derived from the pattern',
     ['A hash of the whole text', 'A sorted copy of the text'], 'Preprocessing the pattern lets the search skip text positions after a mismatch.', 'func.search')

# Drills: stage 05
L = 'function-templates'
rej(L, 'Conflicting deductions', r'''
std::cout << larger(3, 7.5) << "\n";''', '', 'deduced conflicting types', 'No: T is deduced as both int and double',
    ['Yes, and it prints 7.5', 'Yes, and it prints 7'],
    'Each function argument deduces T independently; conflicting deductions make the template non-viable, and no conversion is considered during deduction.',
    decl='template<class T> T larger(T a, T b) { return a < b ? b : a; }')
out(L, 'Template versus non-template', r'''
std::cout << f(1) << " " << f(1L) << " " << f('a') << "\n";''', '', 'plain template template',
    ['plain plain plain', 'template template template'],
    'For f(1) both are exact matches and the non-template wins the tie. For long and char the template deduces an exact match, which beats a conversion or promotion to int.',
    decl='template<class T> const char* f(T) { return "template"; }\nconst char* f(int) { return "plain"; }')
out(L, 'Partial ordering of overloads', r'''
int x = 0;
show(&x);
show(x);
std::cout << "\n";''', '', 'T* T ', ['T T ', 'T* T* '],
    'Both templates are viable for &x; partial ordering prefers show(T*) because it is more specialized. For x only show(T) is viable.',
    decl='template<class T> void show(T) { std::cout << "T "; }\ntemplate<class T> void show(T*) { std::cout << "T* "; }')

L = 'deduction-and-auto'
out(L, 'auto drops top-level const', r'''
const int ci = 1;
auto a = ci;
auto& b = ci;
std::cout << std::is_same_v<decltype(a), int> << std::is_same_v<decltype(b), const int&> << "\n";''', 'type_traits', '11',
    ['01', '10'], 'Plain auto deduces by value and drops top-level const. auto& keeps the low-level const of the referred object.', std=17)
out(L, 'decltype of a parenthesized name', r'''
int x = 0;
std::cout << std::is_same_v<decltype(x), int> << std::is_same_v<decltype((x)), int&> << "\n";''', 'type_traits', '11',
    ['10', '01'], 'decltype(x) names the declared type. decltype((x)) examines an lvalue expression and yields int&.', std=17)
out(L, 'Braced auto initializers', r'''
auto list = {1, 2};
auto single{1};
std::cout << std::is_same_v<decltype(list), std::initializer_list<int>> << std::is_same_v<decltype(single), int> << "\n";''',
    'initializer_list type_traits', '11', ['10', '01'],
    'Copy-list-initialization with auto deduces initializer_list. Since C++17, direct-list-initialization with one element deduces the element type.', std=17)

L = 'specialization'
out(L, 'Top-level const blocks a pointer pattern', r'''
std::cout << K<int*>::v << K<const int*>::v << K<int* const>::v << "\n";''', '', '120', ['122', '121'],
    'const int* matches the more specialized const T* pattern. int* const is a const-qualified type that matches neither pointer pattern, so the primary template is used.',
    decl='template<class T> struct K { static constexpr int v = 0; };\ntemplate<class T> struct K<T*> { static constexpr int v = 1; };\ntemplate<class T> struct K<const T*> { static constexpr int v = 2; };')
out(L, 'Explicit specialization versus overload', r'''
int n = 0;
int* p = &n;
std::cout << f(p) << "\n";''', '', 'overload', ['spec', 'base'],
    'Overload resolution chooses among primary templates first. f(T*) is more specialized than f(T), so the explicit specialization of f(T), declared before f(T*) existed, is never considered.',
    decl='template<class T> const char* f(T) { return "base"; }\ntemplate<> const char* f<int*>(int*) { return "spec"; }\ntemplate<class T> const char* f(T*) { return "overload"; }')
rej(L, 'Partial specialization of a function', r'''
int x = 0;
g(&x);''', '', 'partial specialization', 'No: function templates cannot be partially specialized',
    ['Yes, and it calls the pointer version', 'Yes, but only in C++20'],
    'Only class and variable templates support partial specialization. Write an overload instead.',
    decl='template<class T> void g(T) {}\ntemplate<class T> void g<T*>(T*) {}')

L = 'sfinae'
rej(L, 'Hard error outside the immediate context', r'''
std::cout << f(5) << "\n";''', '', "cannot be used prior to '::'", 'No: instantiating Wrapper<int> is a hard error, not a substitution failure',
    ['Yes, and it prints 2 via the ellipsis overload', 'Yes, and it prints 1'],
    'The failure occurs inside the instantiation of Wrapper<int>, outside the immediate context of f, so SFINAE does not apply.',
    decl='template<class T> struct Wrapper { using type = typename T::value_type; };\ntemplate<class T, class = typename Wrapper<T>::type> int f(T) { return 1; }\nint f(...) { return 2; }')
out(L, 'Expression SFINAE with a fallback', r'''
std::cout << g(std::string("a")) << g(3) << "\n";''', 'string', '12', ['11', '22'],
    'decltype(t.size(), 1) is invalid for int, which removes the template and leaves the ellipsis overload.',
    decl='template<class T> auto g(T t) -> decltype(t.size(), 1) { return 1; }\nint g(...) { return 2; }')
out(L, 'enable_if partitions overloads', r'''
std::cout << kind(true) << " " << kind(1.5f) << "\n";''', 'type_traits', 'integral floating', ['floating floating', 'It is ambiguous'],
    'bool is an integral type, so only the integral overload survives substitution for true.',
    decl='template<class T> std::enable_if_t<std::is_integral<T>::value, const char*> kind(T) { return "integral"; }\ntemplate<class T> std::enable_if_t<std::is_floating_point<T>::value, const char*> kind(T) { return "floating"; }')

L = 'variadic-templates'
out(L, 'sizeof... on an empty pack', r'''
std::cout << count() << count(1, "a", 2.0) << "\n";''', 'cstddef', '03', ['13', '0 3'],
    'sizeof... counts the pack elements at compile time; the empty call has zero.',
    decl='template<class... T> std::size_t count(T...) { return sizeof...(T); }')
out(L, 'Braced-list expansion order', r'''
print(1, 2, 3);
std::cout << "\n";''', '', '123', ['321', 'Unspecified order'],
    'Initializer-clauses of a braced-init-list are sequenced left to right, so the expansion prints in argument order.',
    decl='template<class... T> void print(T... args) {\n    int unused[] = {0, (std::cout << args, 0)...};\n    (void)unused;\n}')
rej(L, 'Missing base case', r'''
std::cout << sum(1, 2) << "\n";''', '', 'no matching function', 'No: the recursion eventually calls sum() with no arguments',
    ['Yes, and it prints 3', 'Yes, but it recurses forever at runtime'],
    'The recursive template needs at least one argument; sum() has no viable candidate.',
    decl='template<class T, class... R> int sum(T first, R... rest) { return first + sum(rest...); }')

L = 'fold-expressions'
out(L, 'Left and right folds with subtraction', r'''
std::cout << left(10, 4, 3) << " " << right(10, 4, 3) << "\n";''', '', '3 9', ['3 3', '9 3'],
    'A left fold groups as ((10-4)-3) and a right fold as 10-(4-3).',
    decl='template<class... T> int left(T... xs) { return (... - xs); }\ntemplate<class... T> int right(T... xs) { return (xs - ...); }')
rej(L, 'Empty unary plus fold', r'''
std::cout << sum() << "\n";''', '', 'empty expansion', 'No: a unary + fold has no value for an empty pack',
    ['Yes, and it prints 0', 'Yes, and it prints nothing'],
    'Only &&, || and the comma operator have defined results for an empty unary fold. Use a binary fold with an initial value.',
    decl='template<class... T> auto sum(T... t) { return (t + ...); }')
out(L, 'Empty && and || folds', r'''
std::cout << all() << any() << "\n";''', '', '10', ['00', '11'],
    'An empty && fold is true and an empty || fold is false: the identities of the operators.',
    decl='template<class... T> bool all(T... t) { return (t && ...); }\ntemplate<class... T> bool any(T... t) { return (t || ...); }')

L = 'concepts'
rej(L, 'Unsatisfied constraint', r'''
std::cout << sq(2.5) << "\n";''', 'concepts', 'constraints not satisfied', 'No: double does not satisfy std::integral',
    ['Yes, it prints 6.25', 'Yes, 2.5 converts to 2 and it prints 4'],
    'Constraints are checked before conversions; the only candidate is removed and clang reports the unsatisfied constraint.',
    decl='template<std::integral T> T sq(T x) { return x * x; }')
out(L, 'Constrained beats unconstrained', r'''
std::cout << f(1) << " " << f(1.0) << "\n";''', 'concepts', 'integral any', ['any any', 'It is ambiguous'],
    'Both templates are equally good for int; the constrained one is more constrained and wins. double satisfies only the unconstrained template.',
    decl='template<class T> const char* f(T) { return "any"; }\ntemplate<std::integral T> const char* f(T) { return "integral"; }')
out(L, 'A requires-expression is a bool', r'''
std::cout << HasSize<std::string> << HasSize<int> << "\n";''', 'string', '10', ['11', 'It does not compile for int'],
    'A requires-expression checks validity without evaluating; invalid expressions make it false rather than an error.',
    decl='template<class T> concept HasSize = requires(T t) { t.size(); };')

L = 'constexpr'
rej(L, 'Runtime argument in a constexpr variable', r'''
int n = 3;
constexpr int r = f(n);
std::cout << r << "\n";''', '', 'must be initialized by a constant expression', 'No: n is not usable in a constant expression',
    ['Yes, f is constexpr so it is evaluated at compile time', 'Yes, but it is evaluated at runtime'],
    'A constexpr variable demands a constant initializer; reading the non-const n is not a constant expression.',
    decl='constexpr int f(int x) { return x * 2; }')
out(L, 'is_constant_evaluated', r'''
constexpr int a = which();
int b = which();
std::cout << a << b << "\n";''', 'type_traits', '12', ['11', '22'],
    'The constexpr initializer is manifestly constant-evaluated; the automatic int b is initialized at runtime.',
    decl='constexpr int which() { return std::is_constant_evaluated() ? 1 : 2; }', std=20)
rej(L, 'Overflow during constant evaluation', r'''
constexpr int bad = std::numeric_limits<int>::max() + 1;
std::cout << bad << "\n";''', 'limits', 'must be initialized by a constant expression', 'No: signed overflow is not allowed in constant evaluation',
    ['Yes, it prints INT_MIN', 'Yes, but the behavior is undefined at runtime'],
    'Undefined behavior disqualifies an expression from being a constant expression, so the compiler must diagnose it.')

L = 'consteval'
rej(L, 'Runtime argument to an immediate function', r'''
int n = 3;
std::cout << sq(n) << "\n";''', '', 'is not a constant expression', 'No: an immediate invocation must be a constant expression',
    ['Yes, it falls back to a runtime call', 'Yes, it prints 9'],
    'Unlike constexpr, consteval has no runtime fallback.',
    decl='consteval int sq(int x) { return x * x; }')
out(L, 'Constant argument in a runtime context', r'''
int r = twice(21);
std::cout << r << "\n";''', '', '42', ['It does not compile', '21'],
    'The immediate invocation twice(21) is itself a constant expression, so it can initialize an ordinary runtime variable.',
    decl='consteval int twice(int x) { return 2 * x; }')
rej(L, 'Address of a consteval function', r'''
auto p = &twice;
std::cout << p(2) << "\n";''', '', 'consteval function', 'No: the address of an immediate function cannot escape to runtime',
    ['Yes, it prints 4', 'Yes, but calling p is undefined'],
    'Taking the address outside an immediate function context is ill-formed.',
    decl='consteval int twice(int x) { return 2 * x; }')

L = 'constinit'
rej(L, 'Dynamic initializer', r'''
std::cout << g << "\n";''', '', 'constant initializer', 'No: runtime() is not a constant expression',
    ['Yes, g is initialized before main', 'Yes, it prints 0'],
    'constinit requires static initialization; a call to a non-constexpr function needs dynamic initialization.',
    decl='int runtime() { return 3; }\nconstinit int g = runtime();')
rej(L, 'constinit on a local variable', r'''
constinit int x = 1;
std::cout << x << "\n";''', '', 'constinit', 'No: constinit applies only to static or thread storage duration',
    ['Yes, it behaves like const', 'Yes, it prints 1'],
    'Automatic variables have no static initialization phase, so constinit is rejected.')
out(L, 'constinit is mutable', r'''
std::cout << bump();
std::cout << bump() << "\n";''', '', '23', ['11', 'It does not compile'],
    'constinit fixes only the initialization; c is not const and can be incremented.',
    decl='constinit int c = 1;\nint bump() { return ++c; }')

L = 'dependent-names'
rej(L, 'Missing typename', r'''
f<std::vector<int>>();''', 'vector', "missing 'typename'", 'No: T::value_type must be marked with typename',
    ['Yes, the compiler infers it is a type', 'Yes, in every standard'],
    'A dependent qualified name is assumed not to name a type unless typename says so, in this declaration context.',
    decl='template<class T> void f() { T::value_type x{}; (void)x; }')
out(L, 'The template disambiguator', r'''
std::cout << call(Holder{}) << "\n";''', '', '3', ['0', 'It does not compile'],
    't.template get<3>() tells the parser that get is a member template, so <3> is a template argument list.',
    decl='struct Holder { template<int N> int get() const { return N; } };\ntemplate<class T> int call(const T& t) { return t.template get<3>(); }')
think(L, 'Concept', 'Why typename exists',
      'Inside template<class T>, how is T::x * p; parsed without typename?',
      'As a multiplication expression, because a dependent name is assumed not to be a type',
      ['As a pointer declaration, because * follows a name', 'The compiler waits until instantiation to decide'],
      'Parsing happens at definition, before T is known; the rule defaults to a non-type, and typename overrides it.')

L = 'detection-idiom'
out(L, 'void_t detects a member', r'''
std::cout << has_size<std::string>::value << has_size<int>::value << "\n";''', 'string type_traits', '10', ['11', '00'],
    'The specialization matches only when decltype(T().size()) is valid; otherwise substitution fails and the primary false_type is used.',
    decl='template<class T, class = void> struct has_size : std::false_type {};\ntemplate<class T> struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};')
out(L, 'Detecting operator<', r'''
std::cout << less_comparable<int>::value << less_comparable<P>::value << "\n";''', 'type_traits utility', '10', ['11', 'It does not compile for P'],
    'P has no operator<, so the decltype expression fails in the immediate context and the false primary template is used.',
    decl='struct P {};\ntemplate<class T, class = void> struct less_comparable : std::false_type {};\ntemplate<class T> struct less_comparable<T, std::void_t<decltype(std::declval<T>() < std::declval<T>())>> : std::true_type {};')
out(L, 'Wrong default argument', r'''
std::cout << has_size<std::string>::value << has_size<int>::value << "\n";''', 'string type_traits', '00', ['10', '11'],
    'has_size<std::string> means has_size<std::string, int>. The specialization produces void, never int, so it never matches.',
    decl='template<class T, class = int> struct has_size : std::false_type {};\ntemplate<class T> struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};')

L = 'crtp'
out(L, 'CRTP hiding', r'''
B b;
std::cout << b.run() << static_cast<Base<B>&>(b).run() << "\n";''', '', '120', ['11', '2020'],
    'B::run hides Base::run for the derived object. Calling through Base<B>& uses Base::run, which statically calls B::step.',
    decl='template<class D> struct Base { int run() { return static_cast<D*>(this)->step() * 10; } };\nstruct B : Base<B> { int step() { return 2; } int run() { return 1; } };')
rej(L, 'Missing derived hook', r'''
D d;
std::cout << d.run() << "\n";''', '', 'no member named', 'No: Base<D>::run requires D::step when instantiated',
    ['Yes, it calls a default step', 'Yes, but it crashes at runtime'],
    'The member function body is instantiated when run is used and the static_cast target lacks step.',
    decl='template<class D> struct Base { int run() { return static_cast<D*>(this)->step(); } };\nstruct D : Base<D> {};')
think(L, 'Code review', 'CRTP in a heterogeneous container',
      'Can objects of A : Base<A> and B : Base<B> be stored together as std::vector<Base*>?',
      'No; Base<A> and Base<B> are unrelated types with no common base',
      ['Yes, CRTP provides virtual dispatch', 'Yes, if Base has a virtual destructor'],
      'CRTP gives static polymorphism. Heterogeneous storage needs a common non-template base or type erasure.')

L = 'invoke'
out(L, 'invoke with member pointers', r'''
P p{5};
std::cout << std::invoke(&P::x, p) << std::invoke(&P::get, &p) << "\n";''', 'functional', '57', ['55', 'It does not compile'],
    'invoke reads a data member pointer from an object and calls a member function pointer through an object pointer.',
    decl='struct P { int x; int get() const { return x + 2; } };')
out(L, 'invoke_result for a data member', r'''
using M = int P::*;
std::cout << std::is_same_v<std::invoke_result_t<M, P&>, int&> << std::is_same_v<std::invoke_result_t<M, P>, int&&> << "\n";''',
    'type_traits', '11', ['10', '00'],
    'Accessing a data member through an lvalue yields an lvalue; through an rvalue it yields an xvalue.',
    decl='struct P { int x; };')
rej(L, 'Calling a member pointer directly', r'''
P p;
std::cout << (&P::get)(p) << "\n";''', '', 'not a function or function pointer', 'No: a member function pointer needs .* or ->* (or std::invoke)',
    ['Yes, it prints 1', 'Yes, p becomes the implicit object'],
    'Ordinary call syntax does not apply to pointers to members.',
    decl='struct P { int get() const { return 1; } };')

L = 'class-template-deduction'
out(L, 'Copy deduction wins', r'''
std::vector v{1, 2, 3};
std::vector w{v};
std::cout << std::is_same_v<decltype(w), std::vector<int>> << " " << w.size() << "\n";''', 'type_traits vector', '1 3',
    ['0 1', '1 1'], 'For a single argument of a vector specialization, the copy deduction candidate is preferred over vector<vector<int>>.')
out(L, 'pair deduces a decayed pointer', r'''
std::pair p{1, "hi"};
std::cout << std::is_same_v<decltype(p.second), const char*> << "\n";''', 'type_traits utility', '1', ['0', 'It does not compile'],
    'pair deduction guides decay arguments, so the array becomes const char*.')
rej(L, 'Nothing to deduce from', r'''
std::vector v;
std::cout << v.size() << "\n";''', 'vector', 'deduc', 'No: there are no arguments to deduce the element type from',
    ['Yes, it is std::vector<int>', 'Yes, it is std::vector<void>'],
    'CTAD needs an initializer; the default constructor gives no information about T.')

L = 'initializer-list-lifetime'
out(L, 'Parentheses versus braces', r'''
std::vector<int> a(3, 1), b{3, 1};
std::cout << a.size() << b.size() << "\n";''', 'vector', '32', ['33', '22'],
    'Braces prefer the initializer_list constructor, producing two elements; parentheses call the count-value constructor.')
out(L, 'Copying an initializer_list', r'''
std::initializer_list<int> a{1, 2};
auto b = a;
std::cout << (a.begin() == b.begin()) << "\n";''', 'initializer_list', '1', ['0', 'It does not compile'],
    'Copying an initializer_list copies the view, not the underlying array.')
san(L, 'asan', 'Assigning a braced list to a stored initializer_list', r'''
int a = 1;
std::initializer_list<int> list;
list = {a, a + 1};
std::cout << *list.begin() << "\n";''', 'initializer_list', 'What happens when *list.begin() is read?',
    'Stack use after scope: the backing array died at the end of the assignment',
    ['It prints 1, because the list keeps its array alive', 'It prints 2'],
    'Only initialization of an initializer_list object extends the backing array; assignment binds to a temporary array that ends with the full-expression.')

# Drills: new stage-05 lessons
L = 'tag-dispatch-traits'
out(L, 'forward_list falls to the input overload', r'''
std::vector<int> v;
std::list<int> l;
std::forward_list<int> f;
std::cout << name(v.begin()) << " " << name(l.begin()) << " " << name(f.begin()) << "\n";''', 'forward_list iterator list vector',
    'random bidirectional input', ['random bidirectional bidirectional', 'random input input'],
    'forward_iterator_tag is not derived from bidirectional_iterator_tag, so its only viable conversion is to the base input_iterator_tag.',
    decl='template<class It> const char* pick(std::random_access_iterator_tag) { return "random"; }\ntemplate<class It> const char* pick(std::bidirectional_iterator_tag) { return "bidirectional"; }\ntemplate<class It> const char* pick(std::input_iterator_tag) { return "input"; }\ntemplate<class It> const char* name(It) { return pick<It>(typename std::iterator_traits<It>::iterator_category{}); }')
out(L, 'decay versus remove_cvref', r'''
std::cout << std::is_same_v<std::remove_cvref_t<const int&>, int> << std::is_same_v<std::decay_t<int[3]>, int*> << std::is_same_v<std::remove_cvref_t<int[3]>, int*> << "\n";''',
    'type_traits', '110', ['111', '100'],
    'decay applies array-to-pointer conversion; remove_cvref only strips references and cv-qualifiers.', std=20)
out(L, 'Dispatching on bool_constant', r'''
std::cout << f(std::is_integral<double>{}) << f(std::is_pointer<int*>{}) << "\n";''', 'type_traits', '01', ['10', 'It is ambiguous'],
    'Each trait derives from true_type or false_type, so the derived-to-base conversion selects the matching overload.',
    decl='int f(std::true_type) { return 1; }\nint f(std::false_type) { return 0; }')

L = 'if-constexpr-branches'
rej(L, 'Discarded branch outside a template', r'''
if constexpr (false) {
    int x = "text";
    (void)x;
}''', '', 'cannot initialize', 'No: outside a template the discarded branch is still checked',
    ['Yes, the branch is discarded', 'Yes, with a warning'],
    'Only inside a template does a discarded statement escape instantiation.')
rej(L, 'Plain if instantiates both branches', r'''
std::cout << f(std::string("a")) << "\n";''', 'string type_traits', 'invalid operands', 'No: v + 1 is instantiated for std::string even though the condition is false',
    ['Yes, it prints 0', 'Yes, because the condition is a constant'],
    'A plain if is a runtime branch; both statements are instantiated even when the condition is constant.',
    decl='template<class T> int f(T v) {\n    if (std::is_integral_v<T>) return v + 1;\n    else return 0;\n}')
out(L, 'Branches with different return types', r'''
int x = 5;
std::cout << get(&x) + get(7) << "\n";''', 'type_traits', '12', ['It does not compile', '5'],
    'Only the selected branch participates in return type deduction, so both specializations return int.',
    decl='template<class T> auto get(T t) {\n    if constexpr (std::is_pointer_v<T>) return *t;\n    else return t;\n}')

L = 'auto-nttp'
out(L, 'Value and type both matter', r'''
std::cout << std::is_same_v<C<5>, C<5u>> << std::is_same_v<C<2 + 3>, C<5>> << "\n";''', 'type_traits', '01', ['11', '00'],
    'The argument type is part of the template argument; equal values of the same type name the same specialization.',
    decl='template<auto N> struct C {};')
rej(L, 'String literal as a template argument', r'''
S<"hi"> s;
(void)s;''', '', 'template argument', 'No: a string literal cannot be a pointer template argument',
    ['Yes, P points to the literal', 'Yes, since C++17'],
    'Template arguments of pointer type must point to complete objects with linkage, not string literals.',
    decl='template<const char* P> struct S {};')
out(L, 'C++20 class and floating NTTPs', r'''
std::cout << get<Fixed{7}>() << " " << twice<1.5> << "\n";''', '', '7 3', ['It does not compile', '7 2'],
    'C++20 accepts structural class types and floating-point types as non-type template parameters.',
    decl='struct Fixed { int v; };\ntemplate<Fixed F> int get() { return F.v; }\ntemplate<double D> constexpr double twice = D * 2;', std=20)

L = 'template-template-params'
out(L, 'Variadic template template parameter', r'''
Make<std::vector> m;
std::cout << m.c.size() << "\n";''', 'vector', '3', ['0', 'It does not compile'],
    'template<class...> class matches templates with any number of type parameters, including vector with its defaulted allocator.',
    decl='template<template<class...> class C> struct Make { C<int> c{1, 2, 3}; };')
ok(L, 'One-parameter template template with std::vector', r'''
One<std::vector> o;
o.c.push_back(1);
std::cout << o.c.size() << "\n";''', 'vector', 'Yes: C++17 lets it match vector because the allocator parameter is defaulted',
    ['No: vector has two template parameters', 'Only with a compiler extension flag'],
    'P0522 (C++17) relaxed template template argument matching; clang enables it by default.',
    decl='template<template<class> class C> struct One { C<int> c; };', std=17)
rej(L, 'Passing a type instead of a template', r'''
Bag<std::vector<int>> b;
(void)b;''', 'vector', 'template template', 'No: std::vector<int> is a type, not a template',
    ['Yes, Container deduces vector', 'Yes, with Container = std::vector<int>'],
    'A template template parameter needs a template name.',
    decl='template<template<class, class> class Container> struct Bag {};')

L = 'variable-templates'
out(L, 'Partially specialized variable template', r'''
std::cout << rank<int**> << rank<int> << "\n";''', '', '20', ['10', '22'],
    'Each pointer layer matches rank<T*> and adds one until the primary template ends the recursion.',
    decl='template<class T> constexpr int rank = 0;\ntemplate<class T> constexpr int rank<T*> = 1 + rank<T>;')
out(L, 'One variable per specialization', r'''
++counter<int>;
++counter<int>;
++counter<long>;
std::cout << counter<int> << counter<long> << counter<char> << "\n";''', '', '210', ['333', '300'],
    'counter<int>, counter<long> and counter<char> are three distinct variables.',
    decl='template<class T> int counter = 0;')
out(L, 'Precision of a variable template', r'''
std::cout << pi<int> << " " << (pi<float> > 3) << "\n";''', '', '3 1', ['4 1', '3 0'],
    'The int specialization truncates; the float specialization keeps the fractional part.',
    decl='template<class T> constexpr T pi = T(3.1415926535897932385L);')

L = 'dependent-base-lookup'
rej(L, 'Base member without this->', r'''
std::cout << D<int>{}.r() << "\n";''', '', 'undeclared identifier', 'No: value is not found because the base is dependent',
    ['Yes, it prints 7', 'Yes, but only with optimization'],
    'Unqualified lookup at definition does not search B<T>, and no other value is visible.',
    decl='template<class T> struct B { int value() const { return 7; } };\ntemplate<class T> struct D : B<T> { int r() const { return value(); } };')
out(L, 'ADL at the point of instantiation', r'''
std::cout << call(n::X{}) << "\n";''', '', 'adl', ['It does not compile', 'generic'],
    'pick(t) is dependent; argument-dependent lookup at instantiation searches namespace n and finds the later declaration.',
    decl='template<class T> const char* call(T t) { return pick(t); }\nnamespace n {\nstruct X {};\nconst char* pick(X) { return "adl"; }\n}')
rej(L, 'No ADL for int', r'''
std::cout << call(1) << "\n";''', '', 'argument-dependent lookup', 'No: int has no associated namespaces and pick was declared after the template',
    ['Yes, ordinary lookup at instantiation finds pick', 'Yes, it prints int'],
    'Non-ADL lookup uses the definition context only; ADL for a fundamental type finds nothing.',
    decl='template<class T> const char* call(T t) { return pick(t); }\nconst char* pick(int) { return "int"; }')

L = 'forwarding-vs-rvalue'
rej(L, 'Class parameter T&& rejects lvalues', r'''
Box<int> b;
int n = 1;
b.take(n);''', '', 'cannot bind to lvalue', 'No: Box<int>::take takes int&&',
    ['Yes, T&& is a forwarding reference', 'Yes, n is copied'],
    'T is fixed by the class; no deduction takes place in the member call.',
    decl='template<class T> struct Box { void take(T&&) {} };')
out(L, 'Greedy forwarding overload', r'''
int n = 1;
const int c = 2;
std::cout << g(n) << " | " << g(c) << "\n";''', '', 'fwd | const ref', ['const ref | const ref', 'fwd | fwd'],
    'For n, T&& deduces int& and is an exact match, better than adding const. For c both are exact, and the non-template wins the tie.',
    decl='template<class T> const char* g(T&&) { return "fwd"; }\nconst char* g(const int&) { return "const ref"; }')
out(L, 'A named rvalue reference is an lvalue', r'''
relay(1);
std::cout << "\n";''', 'utility', 'LR', ['RR', 'LL'],
    'x has a name, so sink(x) sees an lvalue; std::forward<T> restores the original rvalue category.',
    decl='void sink(int&) { std::cout << "L"; }\nvoid sink(int&&) { std::cout << "R"; }\ntemplate<class T> void relay(T&& x) { sink(x); sink(std::forward<T>(x)); }')

L = 'concept-subsumption'
rej(L, 'Repeated expression is not subsumption', r'''
std::cout << f(5) << "\n";''', 'type_traits', 'ambiguous', 'No: the two requires-clauses do not share atomic constraints, so the call is ambiguous',
    ['Yes, it prints wide', 'Yes, it prints integral'],
    'Atomic constraints are identical only when they come from the same expression in the source; textual repetition does not count.',
    decl='template<class T> requires std::is_integral_v<T> const char* f(T) { return "integral"; }\ntemplate<class T> requires (std::is_integral_v<T> && sizeof(T) > 1) const char* f(T) { return "wide"; }')
out(L, 'Subsumption through a named concept', r'''
std::cout << f(5) << " " << f('c') << "\n";''', 'concepts', 'wide integral', ['It is ambiguous', 'wide wide'],
    'Wide is Integral<T> && sizeof(T) > 1, so it subsumes Integral; char fails the size test.',
    decl='template<class T> concept Integral = std::integral<T>;\ntemplate<class T> concept Wide = Integral<T> && (sizeof(T) > 1);\nconst char* f(Integral auto) { return "integral"; }\nconst char* f(Wide auto) { return "wide"; }')
out(L, 'Simple versus nested requirement', r'''
std::cout << Small<long> << Loose<long> << "\n";''', '', '01', ['00', '11'],
    'A simple requirement only checks that sizeof(T) <= 2 is a valid expression. A nested requirement evaluates it.',
    decl='template<class T> concept Small = requires { requires sizeof(T) <= 2; };\ntemplate<class T> concept Loose = requires { sizeof(T) <= 2; };')

L = 'index-sequences'
out(L, 'What make_index_sequence produces', r'''
std::cout << std::make_index_sequence<0>::size() << std::is_same_v<std::make_index_sequence<3>, std::index_sequence<0, 1, 2>> << "\n";''',
    'type_traits utility', '01', ['11', '00'], 'make_index_sequence<N> is an alias for index_sequence<0, ..., N-1>.', std=17)
out(L, 'Reversing a tuple with indices', r'''
printReversed(std::make_tuple(1, 'b', "c"), std::make_index_sequence<3>{});
std::cout << "\n";''', 'tuple utility', 'cb1', ['1bc', 'c b 1'],
    'The fold prints get<2-I> for I = 0, 1, 2 in order.',
    decl='template<class Tuple, std::size_t... I>\nvoid printReversed(const Tuple& t, std::index_sequence<I...>) {\n    ((std::cout << std::get<sizeof...(I) - 1 - I>(t)), ...);\n}', std=17)
rej(L, 'Negative sequence length', r'''
using Bad = std::make_integer_sequence<int, -1>;
std::cout << Bad::size() << "\n";''', 'utility', 'negative', 'No: the length must be non-negative',
    ['Yes, it is empty', 'Yes, it prints 1'], 'make_integer_sequence requires N >= 0.')

L = 'typelists'
out(L, 'Front and PushFront', r'''
using L2 = PushFront<char, TypeList<int>>::type;
std::cout << std::is_same_v<Front<L2>::type, char> << std::is_same_v<L2, TypeList<char, int>> << "\n";''', 'type_traits', '11',
    ['01', '10'], 'PushFront builds a new list type; Front pattern-matches the first element.',
    decl='template<class... T> struct TypeList {};\ntemplate<class L> struct Front;\ntemplate<class H, class... T> struct Front<TypeList<H, T...>> { using type = H; };\ntemplate<class U, class L> struct PushFront;\ntemplate<class U, class... T> struct PushFront<U, TypeList<T...>> { using type = TypeList<U, T...>; };')
out(L, 'Recursive IndexOf', r'''
std::cout << IndexOf<long, TypeList<int, long, double>>::value << "\n";''', 'cstddef', '1', ['2', '0'],
    'The first specialization matches when the head equals U; otherwise the index of the tail is incremented.',
    decl='template<class... T> struct TypeList {};\ntemplate<class U, class L> struct IndexOf;\ntemplate<class U, class... T> struct IndexOf<U, TypeList<U, T...>> { static constexpr std::size_t value = 0; };\ntemplate<class U, class H, class... T> struct IndexOf<U, TypeList<H, T...>> { static constexpr std::size_t value = 1 + IndexOf<U, TypeList<T...>>::value; };')
rej(L, 'Front of an empty list', r'''
using X = Front<TypeList<>>::type;
std::cout << sizeof(X) << "\n";''', '', 'undefined template', 'No: no specialization matches TypeList<>, and the primary is undefined',
    ['Yes, X is void', 'Yes, X is int'],
    'Pattern-matching metafunctions fail with an incomplete type when no case applies.',
    decl='template<class... T> struct TypeList {};\ntemplate<class L> struct Front;\ntemplate<class H, class... T> struct Front<TypeList<H, T...>> { using type = H; };')

L = 'constexpr-allocation'
rej(L, 'Non-transient constexpr vector', r'''
constexpr std::vector<int> v{1, 2};
std::cout << v.size() << "\n";''', 'vector', 'must be initialized by a constant expression', 'No: the vector still owns heap memory when evaluation ends',
    ['Yes, since C++20', 'Yes, the elements are placed in static storage'],
    'Allocations made during constant evaluation must be freed before it completes.')
out(L, 'constexpr std::string', r'''
constexpr std::size_t len = [] {
    std::string s = "ab";
    s += "cd";
    return s.size();
}();
std::cout << len << "\n";''', 'cstddef string', '4', ['It does not compile', '2'],
    'The string is created and destroyed within the constant evaluation; only its size escapes.')
rej(L, 'Leaking new in constant evaluation', r'''
constexpr int x = leak();
std::cout << x << "\n";''', '', 'must be initialized by a constant expression', 'No: the allocation is never deallocated',
    ['Yes, it prints 1', 'Yes, the leak is ignored'],
    'Constant evaluation diagnoses an allocation that is not deallocated.',
    decl='constexpr int leak() { int* p = new int(1); return *p; }')

# Drills: stage 06
L = 'sequence-containers'
san(L, 'asan', 'Reference across reallocation', r'''
std::vector<int> v{1, 2, 3};
v.shrink_to_fit();
int& first = v[0];
v.push_back(4);
std::cout << first << "\n";''', 'vector', 'What happens when first is read?',
    'Heap use after free: push_back reallocated the full vector',
    ['It prints 1, because references follow the element', 'It prints 4'],
    'With size equal to capacity, push_back moves the elements to new storage and frees the old block.')
out(L, 'deque end insertion keeps references', r'''
std::deque<int> d{1, 2};
int& r = d[1];
d.push_front(0);
d.push_back(3);
std::cout << r << " " << d.size() << "\n";''', 'deque', '2 4', ['Undefined: r dangles', '1 4'],
    'Inserting at either end of a deque invalidates iterators but not references to existing elements.')
think(L, 'Complexity', 'Middle insertion in a list',
      'Given only a std::list and a value, what is the cost of inserting the value after its k-th element?',
      'O(k) to reach the position, then O(1) to link the node',
      ['O(1) overall', 'O(n log n)'], 'The constant-time insert assumes you already hold an iterator.', complexity='O(k)')

L = 'ordered-and-hashed'
out(L, 'operator[] inserts during a test', r'''
std::map<std::string, int> m;
if (m["x"] == 0) std::cout << "zero ";
std::cout << m.size() << "\n";''', 'map string', 'zero 1', ['zero 0', '0'],
    'operator[] inserts a value-initialized element for a missing key, even inside a comparison.')
rej(L, 'operator[] on a const map', r'''
const std::map<int, int> m{{1, 2}};
std::cout << m[1] << "\n";''', 'map', 'no viable overloaded', 'No: map::operator[] is non-const because it may insert',
    ['Yes, it prints 2', 'Yes, but it throws if the key is missing'],
    'Use at() or find() on a const map.')
out(L, 'Custom comparator order', r'''
std::map<int, char, std::greater<int>> m{{1, 'a'}, {3, 'c'}, {2, 'b'}};
for (const auto& [k, v] : m) std::cout << v;
std::cout << "\n";''', 'functional map', 'cba', ['abc', 'acb'], 'map iterates in comparator order, here descending keys.')

L = 'ordering-contracts'
out(L, 'Equivalence drops a different element', r'''
std::set<std::pair<int, int>, ByFirst> s{{1, 5}, {1, 7}, {2, 0}};
std::cout << s.size() << " " << s.begin()->second << "\n";''', 'set utility', '2 5', ['3 5', '2 7'],
    'Under ByFirst, (1,5) and (1,7) are equivalent, so the second insertion is rejected.',
    decl='struct ByFirst {\n    bool operator()(const std::pair<int, int>& a, const std::pair<int, int>& b) const { return a.first < b.first; }\n};')
think(L, 'Undefined behavior', 'Sorting with <=',
      'What may std::sort(v.begin(), v.end(), [](int a, int b) { return a <= b; }) do with many equal elements?',
      'Undefined behavior; an implementation may even read outside the range',
      ['Sort correctly but more slowly', 'Throw std::invalid_argument'],
      'Comparators must be irreflexive. Unguarded partition loops rely on comp(x, x) being false.')
out(L, 'stable_sort keeps tie order', r'''
std::vector<std::pair<int, char>> v{{2, 'a'}, {1, 'b'}, {2, 'c'}, {1, 'd'}};
std::stable_sort(v.begin(), v.end(), [](const auto& x, const auto& y) { return x.first < y.first; });
for (const auto& p : v) std::cout << p.second;
std::cout << "\n";''', 'algorithm utility vector', 'bdac', ['badc', 'dbca'],
    'stable_sort preserves the original order among equivalent elements: b before d, a before c.')

L = 'iterator-categories'
rej(L, 'std::sort on a list', r'''
std::list<int> l{3, 1, 2};
std::sort(l.begin(), l.end());''', 'algorithm list', 'invalid operands', 'No: std::sort needs random-access iterators',
    ['Yes, but it is O(n^2)', 'Yes, it calls list::sort'],
    'Use the list::sort member, which relinks nodes.')
out(L, 'Category relationships', r'''
using C = std::iterator_traits<std::list<int>::iterator>::iterator_category;
std::cout << std::is_base_of_v<std::forward_iterator_tag, C> << std::is_base_of_v<std::random_access_iterator_tag, C> << "\n";''',
    'iterator list type_traits', '10', ['11', '01'], 'A bidirectional tag derives from forward but not from random access.', std=17)
think(L, 'Complexity', 'advance on a list',
      'What is the complexity of std::advance(it, n) for a std::list iterator?', 'O(n): it increments n times',
      ['O(1)', 'O(log n)'], 'advance uses += only for random-access iterators.', complexity='O(n)')

L = 'algorithm-erase'
out(L, 'remove does not shrink', r'''
std::vector<int> v{1, 2, 3, 2};
auto end = std::remove(v.begin(), v.end(), 2);
std::cout << v.size() << " " << (end - v.begin()) << "\n";''', 'algorithm vector', '4 2', ['2 2', '4 4'],
    'remove compacts kept values and returns the logical end; size is unchanged until erase.')
out(L, 'std::erase returns a count', r'''
std::vector<int> v{1, 2, 3, 2};
auto n = std::erase(v, 2);
std::cout << n << v.size() << "\n";''', 'vector', '22', ['24', '12'], 'C++20 std::erase removes all matches and returns how many were erased.', std=20)
san(L, 'asan', 'Erase inside a loop', r'''
std::vector<int> v{1, 2};
for (auto it = v.begin(); it != v.end(); ++it)
    if (*it % 2 == 0) v.erase(it);
std::cout << v.size() << "\n";''', 'vector', 'What happens when the last element is erased?',
    'The loop increments past end() and reads outside the allocation',
    ['It prints 1', 'erase returns and the loop ends normally'],
    'After erase, it is invalid; it now equals end(), and ++it skips the termination test. Use it = v.erase(it).')

L = 'ranges-pipelines'
out(L, 'Laziness counts calls', r'''
std::vector<int> v{1, 2, 3};
int calls = 0;
auto view = v | std::views::transform([&](int x) { ++calls; return x * 2; });
std::cout << calls;
for (int x : view) (void)x;
std::cout << calls << "\n";''', 'ranges vector', '03', ['33', '00'],
    'Building the view does no work; each element is transformed when dereferenced.')
out(L, 'Infinite source, finite take', r'''
for (int x : std::views::iota(1) | std::views::filter([](int n) { return n % 2 == 0; }) | std::views::take(3))
    std::cout << x << " ";
std::cout << "\n";''', 'ranges', '2 4 6 ', ['1 2 3 ', 'It never terminates'],
    'take stops after three elements, so the unbounded iota is only partially traversed.')
out(L, 'Piping an rvalue container', r'''
auto view = std::vector<int>{1, 2, 3} | std::views::transform([](int x) { return x * 2; });
for (int x : view) std::cout << x << " ";
std::cout << "\n";''', 'ranges vector', '2 4 6 ', ['Undefined: the vector is destroyed', 'It does not compile'],
    'views::all wraps an rvalue container in owning_view, so the pipeline owns the vector.')

L = 'borrowed-ranges'
rej(L, 'Dangling result from a temporary', r'''
auto it = std::ranges::find(std::vector<int>{1, 2}, 2);
std::cout << *it << "\n";''', 'algorithm vector', 'indirection requires pointer operand', 'No: the result is std::ranges::dangling',
    ['Yes, it prints 2', 'Yes, but it is undefined behavior'],
    'For a non-borrowed rvalue range, range algorithms return dangling instead of an iterator.')
out(L, 'string_view is borrowed', r'''
std::string s = "hello";
auto it = std::ranges::find(std::string_view(s), 'l');
std::cout << *it << *(it + 1) << "\n";''', 'algorithm string string_view', 'll', ['It does not compile', 'lo'],
    'string_view models borrowed_range, so the iterator stays valid while s lives.')
out(L, 'Which ranges are borrowed', r'''
std::cout << std::ranges::borrowed_range<std::string_view> << std::ranges::borrowed_range<std::string> << std::ranges::borrowed_range<std::string&> << "\n";''',
    'ranges string string_view', '101', ['100', '111'], 'Lvalue references are borrowed; an owning string rvalue is not.')

L = 'pmr-resources'
out(L, 'Null upstream on exhaustion', r'''
std::byte buffer[16];
std::pmr::monotonic_buffer_resource arena(buffer, sizeof buffer, std::pmr::null_memory_resource());
std::pmr::vector<int> v(&arena);
try {
    for (int i = 0; i < 10; ++i) v.push_back(i);
    std::cout << "fit\n";
} catch (const std::bad_alloc&) {
    std::cout << "bad_alloc\n";
}''', 'cstddef memory_resource new vector', 'bad_alloc', ['fit', 'It reallocates from the heap'],
    'Monotonic storage is not reused on deallocation, so geometric growth exceeds 16 bytes and the null upstream throws.')
think(L, 'Concept', 'monotonic deallocate',
      'What does monotonic_buffer_resource do when a container deallocates a block?',
      'Nothing; memory is reclaimed only by release() or destruction of the resource',
      ['Returns the block to a free list', 'Returns it to the upstream immediately'],
      'Monotonic resources trade reuse for very cheap allocation.')
out(L, 'Allocator propagation to elements', r'''
std::pmr::monotonic_buffer_resource arena;
std::pmr::vector<std::pmr::string> v(&arena);
v.emplace_back("a string long enough to avoid the small buffer");
std::cout << (v[0].get_allocator().resource() == &arena) << "\n";''', 'memory_resource string vector', '1', ['0', 'It does not compile'],
    'polymorphic_allocator uses uses-allocator construction, passing the resource to pmr::string elements.')

L = 'span'
out(L, 'Static versus dynamic extent size', r'''
std::cout << sizeof(std::span<int, 3>) << " " << sizeof(std::span<int>) << "\n";''', 'span', '8 16', ['16 16', '8 8'],
    'A static extent is in the type, so only a pointer is stored; a dynamic span also stores its size (arm64, 8-byte pointers).', kind='Layout')
rej(L, 'Fixed extent from a vector', r'''
std::vector<int> v{1, 2, 3};
std::span<int, 3> s = v;
std::cout << s.size() << "\n";''', 'span vector', 'no viable conversion', 'No: that constructor is explicit for a static extent',
    ['Yes, it prints 3', 'Yes, but throws if sizes differ'],
    'Constructing a fixed-extent span from a dynamically sized range is explicit, and its size is a precondition.')
san(L, 'asan', 'span over a reallocated vector', r'''
std::vector<int> v{1, 2, 3};
v.shrink_to_fit();
std::span<int> s(v);
v.push_back(4);
std::cout << s[0] << "\n";''', 'span vector', 'What happens when s[0] is read?',
    'Heap use after free: the span still points at the old buffer',
    ['It prints 1, because span tracks the vector', 'It prints 4'], 'span does not own or observe the vector.')

L = 'numeric-algorithms'
out(L, 'Integer accumulator truncates', r'''
std::vector<double> v{0.5, 0.5, 0.5};
std::cout << std::accumulate(v.begin(), v.end(), 0) << "\n";''', 'numeric vector', '0', ['1.5', '1'],
    'The accumulator type comes from the init value: each 0 + 0.5 is converted back to int 0.')
out(L, 'partial_sum', r'''
std::vector<int> v{1, 2, 3, 4};
std::partial_sum(v.begin(), v.end(), v.begin());
for (int x : v) std::cout << x << " ";
std::cout << "\n";''', 'numeric vector', '1 3 6 10 ', ['1 2 3 4 ', '10 9 7 4 '], 'partial_sum writes each running total.')
out(L, 'transform_reduce dot product', r'''
std::vector<int> a{1, 2, 3}, b{4, 5, 6};
std::cout << std::transform_reduce(a.begin(), a.end(), b.begin(), 0) << "\n";''', 'numeric vector', '32', ['21', '90'],
    'The default operations are multiplication and plus: 4 + 10 + 18.')

L = 'sets-and-duplicates'
out(L, 'insert reports duplicates', r'''
std::set<int> s;
std::cout << s.insert(3).second;
std::cout << s.insert(3).second << "\n";''', 'set', '10', ['11', '00'], 'The second pair has false because 3 already exists.')
out(L, 'erase(value) on a multiset', r'''
std::multiset<int> s{1, 2, 2, 2};
auto n = s.erase(2);
std::cout << n << " " << s.size() << "\n";''', 'set', '3 1', ['1 3', '3 4'], 'Erasing by key removes every equivalent element and returns the count.')
out(L, 'erase one occurrence', r'''
std::multiset<int> s{1, 2, 2, 2};
s.erase(s.find(2));
std::cout << s.size() << " " << s.count(2) << "\n";''', 'set', '3 2', ['1 0', '3 3'], 'Erasing an iterator removes exactly one element.')

L = 'priority-queues'
out(L, 'Max heap and min heap', r'''
std::priority_queue<int> maxq;
std::priority_queue<int, std::vector<int>, std::greater<int>> minq;
for (int x : {3, 1, 4}) { maxq.push(x); minq.push(x); }
std::cout << maxq.top() << " " << minq.top() << "\n";''', 'functional queue vector', '4 1', ['1 4', '4 4'],
    'The default less comparator yields the largest element on top; greater reverses that.')
think(L, 'Complexity', 'Priority queue operations',
      'What are the costs of push, pop and top on std::priority_queue?', 'O(log n), O(log n), O(1)',
      ['O(1), O(1), O(1)', 'O(n), O(log n), O(1)'], 'The adaptor maintains a binary heap.', complexity='O(log n)')
out(L, 'Pairs order lexicographically', r'''
std::priority_queue<std::pair<int, char>> q;
q.push({1, 'b'});
q.push({1, 'a'});
q.push({0, 'z'});
std::cout << q.top().first << q.top().second << "\n";''', 'queue utility', '1b', ['1a', '0z'],
    'pair compares first, then second, so (1, b) is the greatest.')

# Drills: new stage-06 lessons
L = 'list-splice'
out(L, 'list::sort keeps iterators', r'''
std::list<int> l{3, 1, 2};
auto it = std::next(l.begin());
l.sort();
std::cout << *it << " " << std::distance(l.begin(), it) << "\n";''', 'iterator list', '1 0', ['1 1', '2 1'],
    'list::sort relinks nodes, so it still refers to the element 1, which is now first.')
san(L, 'asan', 'Using an erased list iterator', r'''
std::list<int> l{1, 2};
auto it = l.begin();
l.erase(it);
std::cout << *it << "\n";''', 'list', 'What happens when *it is evaluated?', 'Heap use after free: the node was destroyed',
    ['It prints 1', 'It prints 2'], 'Erasing a list element invalidates iterators to that element only, and it was one of them.')
think(L, 'Complexity', 'Splicing a range',
      'What is the complexity of a.splice(pos, b, first, last) when a and b are different lists?',
      'Linear in the length of [first, last), to update the sizes',
      ['Constant', 'Linear in a.size() + b.size()'], 'Whole-list and single-node splices are O(1); a range from another list must be counted.', complexity='O(k)')

L = 'hash-load-factor'
out(L, 'reserve prevents rehash', r'''
std::unordered_set<int> s;
s.reserve(100);
auto buckets = s.bucket_count();
for (int i = 0; i < 100; ++i) s.insert(i);
std::cout << (s.bucket_count() == buckets) << "\n";''', 'unordered_set', '1', ['0', 'Unspecified'],
    'reserve(n) guarantees n elements fit without exceeding max_load_factor, so no rehash occurs.')
out(L, 'References survive rehash', r'''
std::unordered_map<int, int> m;
int& ref = m[1];
ref = 7;
m.rehash(1000);
std::cout << ref << "\n";''', 'unordered_map', '7', ['Undefined: rehash invalidates references', '0'],
    'Rehashing invalidates iterators but not pointers or references to elements.')
think(L, 'Complexity', 'Constant hash function',
      'If every key hashes to the same value, what is the cost of find in an unordered_set of n keys?',
      'O(n): all keys share one bucket', ['O(1)', 'O(log n)'],
      'Average constant time depends on a hash that spreads keys across buckets.', complexity='O(n)')

L = 'heterogeneous-lookup'
rej(L, 'find with string_view on a default set', r'''
std::set<std::string> s{"a"};
std::string_view k = "a";
std::cout << (s.find(k) != s.end()) << "\n";''', 'set string string_view', 'no matching member function',
    'No: string_view does not convert implicitly to std::string and less<string> is not transparent',
    ['Yes, it prints 1', 'Yes, but it allocates a temporary'],
    'Only an explicit string construction or a transparent comparator makes this lookup valid.')
out(L, 'contains with a transparent set', r'''
std::set<std::string, std::less<>> s{"apple"};
std::cout << s.contains(std::string_view("apple")) << s.contains("pear") << "\n";''', 'set string string_view', '10',
    ['11', 'It does not compile'], 'std::less<> enables heterogeneous contains.')
out(L, 'Transparent lookup by id', r'''
std::set<Rec, ById> s{{1, "al"}, {2, "bo"}};
std::cout << s.find(2)->name << "\n";''', 'set string', 'bo', ['al', 'It does not compile'],
    'With is_transparent, find(2) uses the mixed overloads of ById without building a Rec.',
    decl='struct Rec { int id; std::string name; };\nstruct ById {\n    using is_transparent = void;\n    bool operator()(const Rec& a, const Rec& b) const { return a.id < b.id; }\n    bool operator()(const Rec& a, int b) const { return a.id < b; }\n    bool operator()(int a, const Rec& b) const { return a < b.id; }\n};', std=14)

L = 'node-handles'
out(L, 'Node handle after a successful insert', r'''
std::map<int, char> a{{1, 'x'}}, b{{2, 'y'}};
auto nh = a.extract(1);
b.insert(std::move(nh));
std::cout << nh.empty() << " " << a.size() << " " << b.size() << "\n";''', 'map utility', '1 0 2', ['0 0 2', '1 1 2'],
    'A successful insert takes ownership, leaving the handle empty.')
out(L, 'Failed node insertion keeps the node', r'''
std::map<int, char> a{{2, 'x'}}, b{{2, 'y'}};
auto r = b.insert(a.extract(2));
std::cout << r.inserted << " " << r.node.mapped() << " " << b[2] << "\n";''', 'map', '0 x y', ['1 x x', '0 y y'],
    'The key exists, so insertion fails and the insert_return_type returns the node to the caller.')
out(L, 'merge leaves conflicts behind', r'''
std::set<int> a{1, 2}, b{2, 3};
a.merge(b);
std::cout << a.size() << b.size() << *b.begin() << "\n";''', 'set', '312', ['402', '303'],
    'Only 3 transfers; the 2 in b conflicts with a and stays.')

L = 'range-projections'
out(L, 'max with a projection', r'''
std::vector<P> v{{"Ada", 3}, {"Cy", 9}, {"Bo", 5}};
std::cout << std::ranges::max(v, {}, &P::score).name << "\n";''', 'algorithm string vector', 'Cy', ['Ada', '9'],
    'The projection compares scores but the algorithm returns the element.',
    decl='struct P { std::string name; int score; };')
rej(L, 'Projection argument to std::sort', r'''
std::vector<P> v{{2}, {1}};
std::sort(v.begin(), v.end(), std::less<>{}, &P::s);''', 'algorithm functional vector', 'no matching function',
    'No: only the std::ranges algorithms take a projection',
    ['Yes, it sorts by s', 'Yes, the extra argument is ignored'],
    'Classic std::sort takes at most a comparator.', decl='struct P { int s; };')
out(L, 'Projection by absolute value', r'''
std::vector<int> v{-3, 1, -2};
std::ranges::sort(v, {}, [](int x) { return std::abs(x); });
for (int x : v) std::cout << x << " ";
std::cout << "\n";''', 'algorithm cstdlib vector', '1 -2 -3 ', ['-3 -2 1 ', '1 -3 -2 '],
    'Elements are compared by |x| but the original values are moved.')

L = 'custom-iterator'
rej(L, 'Missing postfix increment', r'''
std::cout << "ok\n";''', 'cstddef iterator', 'static assertion failed', 'No: forward_iterator requires postfix ++',
    ['Yes, prefix ++ is enough', 'Yes, the concept synthesizes it'],
    'incrementable requires i++ returning the iterator type.',
    decl='struct It {\n    using value_type = int;\n    using difference_type = std::ptrdiff_t;\n    int v = 0;\n    int operator*() const { return v; }\n    It& operator++() { ++v; return *this; }\n    bool operator==(const It&) const = default;\n};\nstatic_assert(std::forward_iterator<It>);')
out(L, 'Classifying standard iterators', r'''
std::cout << std::forward_iterator<int*> << std::random_access_iterator<std::list<int>::iterator> << std::contiguous_iterator<std::vector<int>::iterator> << "\n";''',
    'iterator list vector', '101', ['111', '100'], 'Pointers are contiguous; list iterators are only bidirectional.')
out(L, 'A sentinel of a different type', r'''
const char* text = "hello";
std::cout << std::ranges::distance(std::ranges::subrange(text, NullSentinel{})) << "\n";''', 'iterator ranges', '5', ['6', 'It does not compile'],
    'The sentinel compares equal at the terminating null; C++20 synthesizes the reversed and != comparisons.',
    decl='struct NullSentinel {\n    friend bool operator==(const char* p, NullSentinel) { return *p == 0; }\n};')

L = 'binary-search-bounds'
out(L, 'binary_search and upper_bound past the end', r'''
std::vector<int> v{1, 2, 4};
std::cout << std::binary_search(v.begin(), v.end(), 3) << " " << (std::upper_bound(v.begin(), v.end(), 9) - v.begin()) << "\n";''',
    'algorithm vector', '0 3', ['1 3', '0 2'], 'binary_search returns only a bool; a value larger than all elements has its upper bound at end.')
out(L, 'Bounds on a descending range', r'''
std::vector<int> v{9, 7, 7, 3};
auto lo = std::lower_bound(v.begin(), v.end(), 7, std::greater<>());
auto hi = std::upper_bound(v.begin(), v.end(), 7, std::greater<>());
std::cout << (lo - v.begin()) << " " << (hi - v.begin()) << "\n";''', 'algorithm functional vector', '1 3', ['0 2', 'Undefined: the range is not ascending'],
    'The range is sorted under greater, which is the comparator the bounds use.')
think(L, 'Complexity', 'std::lower_bound on set iterators',
      'What does std::lower_bound(s.begin(), s.end(), x) cost on a std::set of n elements?',
      'O(log n) comparisons but O(n) iterator steps; prefer s.lower_bound(x)',
      ['O(log n) overall', 'O(n log n)'], 'Bidirectional iterators cannot jump to the midpoint.', complexity='O(n)')

L = 'selection-algorithms'
out(L, 'stable_sort by length', r'''
std::vector<std::string> v{"bb", "a", "cc", "d"};
std::stable_sort(v.begin(), v.end(), [](const std::string& x, const std::string& y) { return x.size() < y.size(); });
for (const auto& s : v) std::cout << s << " ";
std::cout << "\n";''', 'algorithm string vector', 'a d bb cc ', ['a d cc bb ', 'd a bb cc '],
    'Equal-length strings keep their input order.')
think(L, 'Complexity', 'Top-k selection',
      'For the k smallest of n values, what are the costs of partial_sort and nth_element?',
      'partial_sort O(n log k); nth_element O(n) on average',
      ['Both O(n log n)', 'partial_sort O(k); nth_element O(log n)'],
      'Use nth_element when the selected set need not be sorted.', complexity='O(n log k)')
out(L, 'nth_element partition guarantee', r'''
std::vector<int> v{9, 1, 8, 2, 7, 3, 6, 4, 5};
auto nth = v.begin() + 4;
std::nth_element(v.begin(), nth, v.end());
bool left = std::all_of(v.begin(), nth, [&](int x) { return x <= *nth; });
bool right = std::all_of(nth, v.end(), [&](int x) { return x >= *nth; });
std::cout << *nth << " " << left << right << "\n";''', 'algorithm vector', '5 11', ['5 10', '9 11'],
    'The median of 1..9 is 5 and the partition guarantee holds on both sides.')

L = 'searchers'
out(L, 'Empty and missing needles', r'''
std::string t = "abc", empty, missing = "z";
std::cout << (std::search(t.begin(), t.end(), empty.begin(), empty.end()) - t.begin()) << " "
          << (std::search(t.begin(), t.end(), missing.begin(), missing.end()) == t.end()) << "\n";''', 'algorithm string', '0 1',
    ['3 1', '0 0'], 'An empty pattern matches at the start; a missing one returns last.')
think(L, 'Complexity', 'When Boyer-Moore pays off',
      'What is the best-case comparison count for Boyer-Moore with a pattern of length m on text of length n?',
      'About n / m, because mismatches let it skip m positions',
      ['Exactly n', 'n times m'], 'Skip tables can jump a whole pattern length after a mismatch on a character not in the pattern.', complexity='O(n/m)')
out(L, 'Calling a searcher directly', r'''
std::string t = "abcabc", n = "cab";
std::boyer_moore_horspool_searcher s(n.begin(), n.end());
auto [first, last] = s(t.begin(), t.end());
std::cout << (first - t.begin()) << " " << (last - first) << "\n";''', 'functional string', '2 3', ['3 3', '2 2'],
    'The searcher returns the matching subrange as a pair of iterators.')
