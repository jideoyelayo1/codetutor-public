"""Additional original C++ units and drills for stages 03-04."""
from cpp_lessons import unit, program
from cpp_drills import drill, main_program

M = main_program
S = '03 Ownership, lifetime, and value semantics'

unit(S,'value-categories-decltype','decltype exposes an expression value category',14,
     'Every expression has a type and a value category. An lvalue designates an object with identity that may not be moved from implicitly, an xvalue designates an object whose resources may be reused, and a prvalue initializes an object or computes a value. glvalue groups lvalues with xvalues; rvalue groups xvalues with prvalues.|decltype applied to a parenthesized expression reports the category in its result type: T& for an lvalue, T&& for an xvalue, and plain T for a prvalue. Without the extra parentheses, decltype(name) reports the declared type of the entity instead. std::move(x) is an xvalue because it returns an rvalue reference; a function returning by value produces a prvalue.|Category is a property of an expression, not of a variable. A named variable declared as T&& is still an lvalue when it appears in an expression, and a string literal is an lvalue array. Reason from the expression form when predicting overload selection or lifetime rules.',
     program('type_traits utility', r'''    int x = 1;
    std::cout << CATEGORY(x) << " " << CATEGORY(std::move(x)) << " " << CATEGORY(make()) << "\n";''',
             r'''template<class T> const char* category() { return std::is_lvalue_reference<T>::value ? "lvalue" : std::is_rvalue_reference<T>::value ? "xvalue" : "prvalue"; }
#define CATEGORY(e) category<decltype((e))>()
int make() { return 4; }
'''),'lvalue xvalue prvalue\n',
     ('Show that casting x to an lvalue reference type produces an lvalue expression.', 'CATEGORY(std::move(x))', 'CATEGORY(static_cast<int&>(x))', 'lvalue lvalue prvalue\n', 'A cast to an lvalue reference type yields an lvalue, so decltype((e)) is int&. The other two expressions are unchanged.'),
     'Why can decltype((x)) differ from decltype(x)?', 'The parentheses make it an expression, so decltype encodes its value category', ['The parentheses create a temporary copy of x','decltype((x)) always yields an rvalue reference'],
     'decltype(id) names the declared type of the entity; decltype((expr)) applies the expression rule, giving int& for the lvalue x.', 'basic.lval')

unit(S,'temporary-lifetime-extension','Reference binding can extend a temporary only directly',14,
     'A temporary normally lives until the end of the full-expression that created it. Binding it directly to a const lvalue reference or an rvalue reference extends its lifetime to that of the reference.|Extension also applies when the reference binds to a member subobject of a temporary obtained by member access, because the complete temporary is then kept alive. It does not apply through a function call that returns a reference, through a reference member initialized in a constructor, or to a temporary bound to a function parameter beyond that call.|A getter returning const std::string& from a temporary object returns a reference into an object that dies at the semicolon. Prefer returning or storing values when a result must outlive the expression, and treat surprising compiled output as unverified rather than as evidence.',
     program('string', r'''    const std::string& kept = make_name();
    std::cout << kept << " " << kept.size() << "\n";''',
             r'''std::string make_name() { return "ada"; }
struct Holder { std::string name; const std::string& get() const { return name; } };
'''),'ada 3\n',
     ('Bind the reference directly to the name member of a temporary Holder.', 'make_name();', 'Holder{"bob"}.name;', 'bob 3\n', 'Member access on a prvalue materializes a temporary Holder; binding a reference to its member subobject extends the complete temporary. Calling get() instead would return a reference whose temporary is destroyed at the semicolon.'),
     'Does const std::string& r = Holder{"x"}.get(); extend the temporary Holder?', 'No; extension does not pass through a function that returns a reference', ['Yes, every const reference extends any temporary in its initializer','Yes, because get() is a const member function'],
     'Only a reference bound directly to the temporary or its subobject extends lifetime. The returned reference is not such a binding.', 'class.temporary')

unit(S,'rule-of-five','Write all five operations for a raw owning resource',14,
     'A class that directly owns a raw resource needs a destructor to release it, a copy constructor and copy assignment that duplicate or forbid duplication, and a move constructor and move assignment that transfer ownership and leave the source releasable.|Copy assignment must keep the target valid if allocation throws, so allocate the new storage before releasing the old one. Move operations that only exchange pointers should be noexcept so standard containers can rely on them. The moved-from object here holds a null pointer and size zero, which its destructor can release safely.|Prefer the rule of zero by wrapping the resource in an existing owner such as std::vector or std::unique_ptr. Writing five members by hand is a maintenance boundary: a destructor plus implicit copying would make two objects delete the same pointer.',
     program('algorithm cstddef', r'''    Buffer a(3);
    Buffer b(a);
    Buffer c(std::move(a));
    b = c;
    a = std::move(b);
    std::cout << a.size() << " " << b.size() << "\n";''',
             r'''class Buffer {
    std::size_t n_;
    int* data_;
public:
    explicit Buffer(std::size_t n) : n_(n), data_(new int[n]()) {}
    ~Buffer() { delete[] data_; }
    Buffer(const Buffer& o) : n_(o.n_), data_(new int[o.n_]) { std::copy(o.data_, o.data_ + n_, data_); std::cout << "copy "; }
    Buffer(Buffer&& o) noexcept : n_(o.n_), data_(o.data_) { o.n_ = 0; o.data_ = nullptr; std::cout << "move "; }
    Buffer& operator=(const Buffer& o) {
        if (this != &o) { int* fresh = new int[o.n_]; std::copy(o.data_, o.data_ + o.n_, fresh); delete[] data_; data_ = fresh; n_ = o.n_; }
        std::cout << "copy= "; return *this;
    }
    Buffer& operator=(Buffer&& o) noexcept {
        if (this != &o) { delete[] data_; data_ = o.data_; n_ = o.n_; o.data_ = nullptr; o.n_ = 0; }
        std::cout << "move= "; return *this;
    }
    std::size_t size() const { return n_; }
};
'''),'copy move copy= move= 3 0\n',
     ('Construct c by copying a instead of moving from it.', 'Buffer c(std::move(a));', 'Buffer c(a);', 'copy copy copy= move= 3 0\n', 'The lvalue a selects the copy constructor, so a keeps its storage until the final move assignment takes b\'s buffer and leaves b empty.'),
     'A class frees an owning raw pointer in its destructor but leaves copying implicit. What happens when it is copied and both copies are destroyed?', 'Both objects hold the same pointer and both delete it, which is undefined behavior', ['The implicit copy constructor allocates a fresh buffer','The compiler rejects the implicit copy'],
     'The implicit copy constructor copies the pointer member. Two destructors then release one allocation.', 'class.copy.ctor')

unit(S,'copy-and-swap','Copy-and-swap commits assignment with a nonthrowing swap',14,
     'The copy-and-swap idiom takes the assignment source by value and swaps the parameter with the target. Constructing the parameter performs any copy or move; swapping then exchanges representations, and the old state is released when the parameter is destroyed.|Because every operation that can throw happens while constructing the parameter, the target is unchanged if it fails: the strong exception guarantee. Self-assignment needs no special test because the parameter is an independent copy. One by-value operator serves both lvalue and rvalue sources.|The idiom always builds a complete new representation, so it cannot reuse existing capacity and may cost more than a hand-written assignment. swap must not throw; if it could, the guarantee would be lost.',
     program('initializer_list string vector', r'''    Names a{"x", "y"};
    Names b{"z"};
    b = a;
    Names& alias = a;
    a = alias;
    std::cout << a.size() << " " << b.size() << "\n";''',
             r'''class Names {
    std::vector<std::string> items_;
public:
    Names(std::initializer_list<std::string> init) : items_(init) {}
    Names(const Names&) = default;
    Names(Names&&) noexcept = default;
    Names& operator=(Names other) noexcept { swap(other); return *this; }
    void swap(Names& other) noexcept { items_.swap(other.items_); }
    std::size_t size() const { return items_.size(); }
};
'''),'2 2\n',
     ('Assign a temporary three-element Names to b instead of copying a.', 'b = a;', 'b = Names{"p", "q", "r"};', '2 3\n', 'The temporary initializes the by-value parameter, and the noexcept swap installs its three elements in b. The self-assignment of a remains harmless.'),
     'Why does operator=(Names other) give the strong exception guarantee?', 'Any throwing copy happens while constructing the parameter, before the target changes', ['swap catches every exception internally','The compiler rolls back members after an exception'],
     'The target is modified only by the nonthrowing swap. A failed copy leaves the target untouched.', 'class.copy.assign')

unit(S,'placement-new-launder','Placement new starts a lifetime the program must end',17,
     'A placement new-expression constructs an object in storage the program already provides. It does not allocate, and the storage must be large enough and suitably aligned for the type. alignas on a byte array supplies that alignment.|The program owns the object lifetime: it must call the destructor explicitly before the storage is reused or goes away. A pointer to the old storage, such as a reinterpret_cast of the byte array, does not automatically point to the new object; std::launder (C++17) obtains a usable pointer to the object now living at that address.|Forgetting the destructor skips cleanup silently. Constructing into misaligned or undersized storage, or reading through a stale pointer after replacing an object with const or reference members, has undefined behavior. Prefer std::optional, std::variant, or a container unless you are implementing such a facility.',
     program('new', r'''    alignas(Point) unsigned char storage[sizeof(Point)];
    Point* p = new (storage) Point(3, 4);
    std::cout << p->x + p->y << " ";
    Point* again = std::launder(reinterpret_cast<Point*>(storage));
    std::cout << again->y << " ";
    p->~Point();''',
             r'''struct Point {
    int x, y;
    Point(int a, int b) : x(a), y(b) { std::cout << "built "; }
    ~Point() { std::cout << "destroyed\n"; }
};
'''),'built 7 4 destroyed\n',
     ('After destroying the first Point, construct a second one in the same storage and destroy it too.', 'p->~Point();', 'p->~Point();\n    Point* q = new (storage) Point(5, 6);\n    std::cout << q->x << " ";\n    q->~Point();', 'built 7 4 destroyed\nbuilt 5 destroyed\n', 'The storage is reused only after the first lifetime has ended. The second object again needs its own explicit destructor call.'),
     'Who runs the destructor of an object created with placement new in a local byte array?', 'The program, with an explicit destructor call', ['The byte array runs it automatically at scope exit','delete p, because new created it'],
     'The array has no knowledge of the object built inside it. delete would try to free storage that was never allocated by operator new.', 'ptr.launder')

unit(S,'new-delete-pairing','Release each new-expression with its matching delete',14,
     'new T creates one object and must be released with delete. new T[n] creates an array and must be released with delete[], which destroys every element in reverse order before freeing the storage.|Implementations often store the element count before an array of class type with a nontrivial destructor, so the pointer returned by new[] is not the start of the allocation. Passing it to the single-object delete can free the wrong address. Mixing malloc/free with new/delete is equally wrong.|Every mismatch is undefined behavior even if a particular run seems fine. Prefer std::make_unique<T>(), std::make_unique<T[]>(n), or std::vector<T>, which pair allocation and release automatically.',
     program('memory', r'''    Tracked* one = new Tracked;
    Tracked* many = new Tracked[3];
    delete one;
    delete[] many;
    std::cout << Tracked::destroyed << "\n";''',
             r'''struct Tracked { ~Tracked() { ++destroyed; } static int destroyed; };
int Tracked::destroyed = 0;
'''),'4\n',
     ('Replace the manual new/delete pairs with scoped unique_ptr owners.', 'Tracked* one = new Tracked;\n    Tracked* many = new Tracked[3];\n    delete one;\n    delete[] many;', '{\n        auto one = std::make_unique<Tracked>();\n        auto many = std::make_unique<Tracked[]>(3);\n    }', '4\n', 'unique_ptr<T> uses delete and unique_ptr<T[]> uses delete[]; leaving the block destroys all four objects.'),
     'What is wrong with delete p when p came from new Tracked[3]?', 'Undefined behavior: an array new-expression must be released with delete[]', ['Only the first element is leaked, which is otherwise valid','Nothing; delete and delete[] are interchangeable for class types'],
     'The delete form must match the new form. The single-object form does not know the element count or array layout.', 'expr.delete')

unit(S,'noexcept-move-growth','Vector growth copies when moving might throw',14,
     'When std::vector reallocates, it must transfer existing elements into new storage. To keep push_back and emplace_back strongly exception safe, it uses the move constructor only when that constructor is noexcept or the type cannot be copied; otherwise it copies.|std::move_if_noexcept encodes this choice. A move constructor is noexcept when declared so, or when it is defaulted and every member and base move is noexcept. A user-written move constructor without noexcept is assumed to be able to throw.|A forgotten noexcept can silently turn every reallocation into deep copies. Mark move operations noexcept only when they truly cannot throw; a lie would call std::terminate instead of reporting an error.',
     program('vector', r'''    std::vector<Item> items;
    items.reserve(1);
    items.emplace_back();
    items.emplace_back();
    std::cout << "copies " << Item::copies << " moves " << Item::moves << "\n";''',
             r'''struct Item {
    static int copies, moves;
    Item() = default;
    Item(const Item&) { ++copies; }
    Item(Item&&) { ++moves; }
};
int Item::copies = 0;
int Item::moves = 0;
'''),'copies 1 moves 0\n',
     ('Declare the move constructor noexcept and observe the reallocation.', 'Item(Item&&) {', 'Item(Item&&) noexcept {', 'copies 0 moves 1\n', 'With a nonthrowing move constructor, vector can move the existing element without risking a half-transferred buffer.'),
     'Why does vector copy the existing element during growth here?', 'The move constructor may throw and a copy constructor exists, so vector copies to keep the strong guarantee', ['Vectors never move elements during reallocation','emplace_back always copies its arguments'],
     'move_if_noexcept selects copying for a potentially throwing move when a copy is available.', 'vector.modifiers')

unit(S,'shared-from-this','make_shared and enable_shared_from_this share one control block',14,
     'std::make_shared typically performs one allocation holding both the reference-count control block and the object. Separate new plus shared_ptr construction needs two allocations. With make_shared, the object storage is reclaimed only when both the strong and the weak counts reach zero, although the object itself is destroyed when the last shared_ptr goes away.|A class deriving from std::enable_shared_from_this<T> can call shared_from_this() to obtain a shared_ptr that joins the existing ownership group. Building a new shared_ptr from this would create a second, independent control block and a double delete.|shared_from_this requires that a shared_ptr already owns the object. Since C++17 it throws std::bad_weak_ptr otherwise; before C++17 the behavior was undefined. Do not call it from the constructor, where no owner exists yet.',
     program('memory', r'''    auto session = std::make_shared<Session>();
    auto again = session->self();
    const bool same = again == session;
    std::cout << session.use_count() << " " << same << "\n";''',
             r'''struct Session : std::enable_shared_from_this<Session> {
    std::shared_ptr<Session> self() { return shared_from_this(); }
};
'''),'2 1\n',
     ('Release the second handle before reporting the count.', 'const bool same = again == session;', 'const bool same = again == session;\n    again.reset();', '1 1\n', 'Both handles shared one control block, so resetting one leaves a single strong owner.'),
     'What does make_shared typically allocate?', 'One block holding both the control block and the object', ['Two separate blocks, one for the count and one for the object','Nothing until the shared_ptr is first copied'],
     'Combining the allocations is the usual implementation and the standard recommends it. It also ties the storage lifetime to outstanding weak_ptrs.', 'util.smartptr.enab')

unit(S,'moved-from-state','Moved-from objects keep a documented minimal contract',14,
     'After a move, the source object still exists and its destructor will run. Standard library types leave it in a valid but unspecified state unless a stronger rule is documented, so operations without preconditions remain safe.|Some types specify more: a moved-from std::unique_ptr or std::shared_ptr is empty. A moved-from std::string or std::vector has some valid value; assign, clear, or destroy it before relying on its contents.|Using a moved-from object is not use-after-free. The real errors are calling an operation with an unmet precondition, such as dereferencing an empty unique_ptr or calling front() on a possibly empty container. Your own types should document what a moved-from object supports.',
     program('memory string', r'''    std::unique_ptr<int> owner = std::make_unique<int>(5);
    std::unique_ptr<int> taker = std::move(owner);
    std::string text = "payload";
    std::string other = std::move(text);
    text = "reset";
    std::cout << (owner == nullptr) << " " << *taker << " " << text << "\n";''',
             ''),'1 5 reset\n',
     ('Instead of assigning, clear the moved-from string and append new text.', 'text = "reset";', 'text.clear();\n    text += "again";', '1 5 again\n', 'clear has no precondition, so it establishes a known empty value before the append.'),
     'Which operation is safe on a moved-from std::string without further checks?', 'Assigning a new value or calling clear()', ['Reading s[0] because the string is guaranteed to keep its old value','Nothing; touching it is undefined behavior'],
     'Valid but unspecified means operations without preconditions work; reading a particular value does not.', 'lib.types.movedfrom')

unit(S,'dangling-temporaries','Views and references must not outlive their temporaries',17,
     'A std::string_view, span, or plain reference records where data lives but not who keeps it alive. Initializing one from a temporary std::string leaves it pointing into storage that is freed at the end of the full-expression.|Lifetime extension does not help, because a view object is not a reference binding to the temporary. The same hazard appears when a function returns a view or reference into a local or a parameter, and in a range-based for loop over a member of a temporary before C++23.|Keep an owning object alive for at least as long as every view of it. String literals have static storage duration, so views of them are safe. Treat any view parameter as borrowed for the call only unless the interface states otherwise.',
     program('string string_view', r'''    const std::string owner = make_label();
    std::string_view view = owner;
    std::cout << view.substr(0, 4) << "\n";''',
             r'''std::string make_label() { return "temporary"; }
'''),'temp\n',
     ('View a string literal directly instead of an owned string.', 'const std::string owner = make_label();\n    std::string_view view = owner;', 'std::string_view view = "literal";', 'lite\n', 'A string literal lives for the whole program, so the view needs no separate owner.'),
     'Why does std::string_view v = make_label(); dangle?', 'The temporary string is destroyed at the end of the full-expression and a view does not extend its lifetime', ['string_view copies the characters, so it never dangles','The compiler always extends the temporary to the scope of v'],
     'Only references bound directly to a temporary extend it. string_view is a separate object holding a pointer and length.', 'string.view')

S = '04 Objects, interfaces, and software design'
D = []

unit(S,'virtual-dispatch-cost','Virtual dispatch selects by dynamic type at a measurable cost',14,
     'A call to a virtual function through a reference or pointer selects the final overrider for the dynamic type of the object. Common implementations store a hidden pointer in each polymorphic object to a per-class table of function addresses.|The hidden pointer usually enlarges every object, and the call is indirect. The larger cost is often lost inlining: unless the compiler can prove the dynamic type, it cannot see the target body. A qualified call such as obj.Base::f() names a function directly and bypasses dispatch.|Calling through an object by value slices the derived part and calls the base version. Measure before replacing virtual calls for speed; final classes, sealed hierarchies, std::variant, or templates trade openness for static knowledge.',
     program('', r'''    Circle c;
    show(c);
    std::cout << c.Shape::name() << " " << (sizeof(Dynamic) > sizeof(Plain)) << "\n";''',
             r'''struct Shape { virtual ~Shape() = default; virtual const char* name() const { return "shape"; } };
struct Circle : Shape { const char* name() const override { return "circle"; } };
struct Plain { int value; };
struct Dynamic { virtual ~Dynamic() = default; int value; };
void show(const Shape& s) { std::cout << s.name() << " "; }
'''),'circle shape 1\n',
     ('Change show to take its Shape by value and observe the call.', 'void show(const Shape& s)', 'void show(Shape s)', 'shape shape 1\n', 'Copying into a Shape parameter creates a Shape object, so its dynamic type is Shape and dispatch selects Shape::name.'),
     'What does the qualified call c.Shape::name() do?', 'Calls Shape::name directly, bypassing virtual dispatch', ['Dispatches to Circle::name through the table','Fails to compile because name is virtual'],
     'A qualified-id suppresses the virtual call mechanism.', 'class.virtual',D)

unit(S,'virtual-base-diamond','Virtual inheritance shares one base subobject',14,
     'With ordinary multiple inheritance, a class reaching the same base through two paths contains two separate base subobjects. Unqualified access to a member of that base is then ambiguous.|Declaring the inheritance virtual makes all virtual paths share one subobject. The most derived class constructs that shared base before any non-virtual base, and an intermediate class\'s initializer for it is ignored when it is not the most derived class.|Virtual bases add indirection to locate the shared subobject and complicate construction. Prefer composition or interfaces without data; use virtual inheritance deliberately when one shared base state is actually required.',
     program('', r'''    Port port;
    std::cout << Device::built << " " << port.Reader::id << "\n";''',
             r'''struct Device { Device() { ++built; } static int built; int id = 7; };
int Device::built = 0;
struct Reader : Device {};
struct Writer : Device {};
struct Port : Reader, Writer {};
'''),'2 7\n',
     ('Make both Reader and Writer inherit Device virtually.', [('struct Reader : Device', 'struct Reader : virtual Device'), ('struct Writer : Device', 'struct Writer : virtual Device')], '', '1 7\n', 'Both paths now refer to one shared Device subobject, constructed once by Port.'),
     'Why is port.id ill-formed in the non-virtual diamond?', 'Port contains two Device subobjects, so the name is ambiguous', ['id is private in Device','Static members cannot coexist with data members'],
     'Name lookup finds id in two distinct base subobjects. Qualifying the path or using virtual inheritance resolves it.', 'class.mi',D)

unit(S,'padding-and-empty-members','Member order, padding, and empty members decide object size',20,
     'Each member must sit at an offset that is a multiple of its alignment, so the compiler inserts padding between members and at the end. The size of a class is a multiple of its strictest member alignment so that arrays keep every element aligned. Ordering members from largest to smallest alignment often removes padding.|Every complete object has a nonzero size, so an empty member still occupies at least one byte plus padding. An empty base can occupy no storage (the empty base optimization). C++20 [[no_unique_address]] allows an empty member to overlap other members in the same way, which suits stateless allocators, comparators, and policies.|Exact numbers are an ABI property; the values shown are those of common LP64 ABIs such as arm64 and x86-64. Two subobjects of the same empty type still need distinct addresses. Do not serialize raw layout or depend on sizes without static_assert.',
     program('', r'''    std::cout << sizeof(Loose) << " " << sizeof(Packed) << " " << alignof(int) << "\n";
    std::cout << sizeof(WithEmpty) << " " << sizeof(NoAddress) << "\n";''',
             r'''struct Loose { char a; int b; char c; };
struct Packed { int b; char a; char c; };
struct Empty {};
struct WithEmpty { Empty tag; int value; };
struct NoAddress { [[no_unique_address]] Empty tag; int value; };
'''),'12 8 4\n8 4\n',
     ('Add a double as the first member of Packed and predict its new size.', 'struct Packed { int b;', 'struct Packed { double d; int b;', '12 16 4\n8 4\n', 'Eight bytes of double, four of int, and two chars total fourteen; the size rounds up to the 8-byte alignment of double.'),
     'Why is sizeof(Loose) 12 on common LP64 ABIs?', 'Padding aligns int b to 4 bytes and rounds the size to a multiple of its alignment', ['char members are each stored in 4 bytes','The compiler adds a hidden pointer to every struct'],
     'char a at 0, three bytes of padding, int b at 4, char c at 8, then tail padding to 12.', 'dcl.attr.nouniqueaddr',D)

unit(S,'override-and-final','override and final turn silent mismatches into errors',14,
     'A function overrides a base virtual only if its name, parameter types, cv-qualifiers, and ref-qualifier match. A small mismatch, such as long instead of int or a missing const, declares a new function that hides the base version instead.|override asks the compiler to verify that the function really overrides something. final on a virtual function forbids further overriding, and final on a class forbids deriving from it; both also tell the optimizer the dynamic target is known.|Use override on every overriding declaration so interface changes break the build rather than behavior. Apply final where extension is genuinely not intended; it is a design commitment that later subclasses cannot undo.',
     program('', r'''    FileLogger file;
    const Logger& log = file;
    log.write(2);''',
             r'''struct Logger { virtual ~Logger() = default; virtual void write(int level) const { std::cout << "base " << level << "\n"; } };
struct FileLogger final : Logger { void write(int level) const override { std::cout << "file " << level << "\n"; } };
'''),'file 2\n',
     ('Remove override and change the parameter to long to see a silent mismatch.', 'void write(int level) const override', 'void write(long level) const', 'base 2\n', 'write(long) is a different function. It hides the base name in FileLogger but does not override, so the call through Logger runs the base version.'),
     'What does override add to a member declaration?', 'A compile error if the function does not override a base virtual function', ['It makes the function virtual in the base class','It changes the call to static dispatch'],
     'override is a checked assertion about overriding; it does not change which function a correct override calls.', 'class.virtual',D)

unit(S,'pimpl-firewall','Pimpl hides a representation behind one owning pointer',14,
     'The pointer-to-implementation idiom moves private data into a separately defined Impl struct and keeps only a pointer to it in the public class. Clients include a header that never changes when Impl changes, which reduces rebuilds and keeps the class layout stable.|std::unique_ptr<Impl> needs the complete Impl type wherever its deleter is instantiated. Declare the destructor and move operations in the class and define them, even as = default, after Impl is complete in the implementation file. Copying must be written explicitly if it is wanted.|The cost is one allocation per object and an extra indirection on every access. A moved-from object holds a null pointer, so member functions must document whether they may be called on it.',
     program('memory utility', r'''    Widget a;
    Widget b = std::move(a);
    std::cout << b.area() << "\n";''',
             r'''class Widget {
public:
    Widget();
    ~Widget();
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;
    int area() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
// The definitions below would live in widget.cpp.
struct Widget::Impl { int w = 3, h = 4; };
Widget::Widget() : impl_(std::make_unique<Impl>()) {}
Widget::~Widget() = default;
Widget::Widget(Widget&&) noexcept = default;
Widget& Widget::operator=(Widget&&) noexcept = default;
int Widget::area() const { return impl_->w * impl_->h; }
'''),'12\n',
     ('Change the private representation without touching the public class definition.', 'int w = 3, h = 4;', 'int w = 5, h = 4;', '20\n', 'Only Widget::Impl changed. In a multi-file build, clients of the Widget header would not need recompiling.'),
     'Why are ~Widget() and the move operations defined after Impl is complete?', 'unique_ptr\'s default deleter needs the complete Impl type where it is instantiated', ['Defaulted functions cannot appear inside a class','Impl must be public for unique_ptr to work'],
     'Instantiating the deleter inside the class definition would apply sizeof and delete to an incomplete type and fail to compile.', 'unique.ptr.dltr.dflt',D)

unit(S,'implicit-move-suppression','Declaring a destructor suppresses the implicit move',14,
     'The compiler implicitly declares a move constructor and move assignment only if the class declares no copy constructor, copy assignment, move operation of the other kind, or destructor. Declaring any of them, even as = default, suppresses the implicit moves.|Without a move constructor, an rvalue argument binds to the const copy constructor instead, so std::move quietly copies. Declaring a move constructor or move assignment, in turn, defines the implicit copy operations as deleted.|An empty destructor added for logging or as a breakpoint can therefore turn moves into copies throughout a program. Either follow the rule of zero, or explicitly default all the operations you want.',
     program('utility', r'''    Holder a;
    Holder b = std::move(a);
    (void)b;''',
             r'''struct Probe {
    Probe() = default;
    Probe(const Probe&) { std::cout << "copy\n"; }
    Probe(Probe&&) noexcept { std::cout << "move\n"; }
};
struct Holder {
    Probe probe;
    ~Holder() {}
};
'''),'copy\n',
     ('Remove the user-declared destructor from Holder.', '    ~Holder() {}\n', '', 'move\n', 'With no user-declared special member, Holder gets an implicit move constructor that moves its Probe member.'),
     'Why does Holder b = std::move(a); copy the Probe in the original program?', 'The user-declared destructor suppresses Holder\'s implicit move constructor, so the copy constructor is used', ['std::move does not work on class types','Probe\'s move constructor is noexcept, which forbids moving'],
     'The rvalue binds to const Holder& because no move constructor was declared.', 'class.copy.ctor',D)

unit(S,'explicit-conversions','explicit restricts conversions to deliberate contexts',14,
     'A constructor callable with one argument is also an implicit conversion unless it is marked explicit. Implicit conversions let unrelated values flow into function parameters and comparisons without a visible cast.|explicit constructors still work in direct initialization such as Meters{1.5} and static_cast. An explicit operator bool can still be used where the language performs a contextual conversion: if and while conditions, the operands of !, && and the logical-or operator, and the conditional operator\'s first operand.|Make single-argument constructors and conversion operators explicit by default. Allow implicit conversions only when the source and target represent the same abstract value, as with a string literal to a string type.',
     program('', r'''    Handle open{3}, closed{-1};
    std::cout << twice(Meters{1.5}) << " " << (open ? "open" : "closed") << " " << !closed << "\n";''',
             r'''struct Meters { explicit Meters(double v) : value(v) {} double value; };
struct Handle { int fd; explicit operator bool() const { return fd >= 0; } };
double twice(Meters m) { return m.value * 2; }
'''),'3 open 1\n',
     ('Test the closed handle in a conditional expression as well.', '!closed', '(closed ? "open" : "closed")', '3 open closed\n', 'The conditional operator contextually converts its first operand, so the explicit operator bool is allowed there.'),
     'Which statement compiles with these types?', 'if (open) {}', ['bool b = open;','twice(1.5);'],
     'An if condition is a contextual conversion. Copy-initializing a bool and implicitly converting 1.5 to Meters are both blocked by explicit.', 'class.conv.fct',D)

unit(S,'inline-static-members','Inline static data members are defined in the class',17,
     'A static data member belongs to the class, not to any object, so there is exactly one copy shared by all instances and it does not contribute to sizeof.|Before C++17, a non-const static data member declared in the class also needed one out-of-class definition in exactly one translation unit. Since C++17, inline static allows the in-class declaration to be the definition, and constexpr static data members are implicitly inline.|A shared mutable counter is global state: unsynchronized access from several threads is a data race, and tests can interfere through it. Static initialization order across translation units remains a separate hazard.',
     program('', r'''    Connection a;
    {
        Connection b;
        std::cout << Connection::live << "/" << Connection::limit << " ";
    }
    std::cout << Connection::live << "\n";''',
             r'''struct Connection {
    inline static int live = 0;
    static constexpr int limit = 2;
    Connection() { ++live; }
    ~Connection() { --live; }
};
'''),'2/2 1\n',
     ('Create two connections in the inner scope.', 'Connection b;', 'Connection b, c;', '3/2 1\n', 'Every constructor increments the one shared counter, and both inner destructors decrement it at the closing brace.'),
     'What does inline static change compared with a C++14 static data member?', 'The in-class declaration is a definition, so no separate out-of-class definition is needed', ['Each object gets its own copy of the member','The member becomes thread-local'],
     'inline applies the one-definition rule for inline entities to the variable, permitting a definition in a header.', 'class.static.data',D)

unit(S,'user-defined-literals','User-defined literals attach units to constants',14,
     'A literal operator such as operator""_km lets a numeric or string literal carry a suffix that produces a domain type. Integer literals select a parameter of type unsigned long long, floating literals select long double, and string literals select a pointer plus a length.|The suffix applies to the literal token only. In -5_m, the minus sign is a unary operator applied to the result, so the domain type needs its own operator-. Literal operators can be constexpr, making unit-safe constants available at compile time.|Suffixes that do not begin with an underscore are reserved for the standard library, such as the s suffix for std::string and the chrono suffixes. Keep user literal operators in a namespace and bring them in with a using-directive where they are needed.',
     program('', r'''    const Distance trip = 1.5_km + 250_m;
    std::cout << static_cast<int>(trip.meters) << "\n";''',
             r'''struct Distance { long double meters; };
constexpr Distance operator""_km(long double v) { return Distance{v * 1000}; }
constexpr Distance operator""_m(unsigned long long v) { return Distance{static_cast<long double>(v)}; }
Distance operator+(Distance a, Distance b) { return Distance{a.meters + b.meters}; }
'''),'1750\n',
     ('Compute a trip of 2.0 kilometres plus 5 metres.', '1.5_km + 250_m', '2.0_km + 5_m', '2005\n', 'The floating literal uses the long double operator and the integer literal uses the unsigned long long operator.'),
     'Why must user-defined literal suffixes start with an underscore?', 'Suffixes without an underscore are reserved for the standard library', ['The underscore marks the operator as constexpr','Without it the literal is parsed as a macro'],
     'Programs that declare non-underscore suffixes use reserved names.', 'over.literal',D)

unit(S,'construction-dispatch','Virtual calls in constructors use the class under construction',14,
     'While a base-class constructor or destructor runs, the object\'s dynamic type is that base class. Virtual calls made from it, directly or indirectly, dispatch to the version for the class whose constructor or destructor is running, not to a more derived override.|This is deliberate: the derived members are not yet constructed, or are already destroyed, so a derived override could read invalid state. typeid and dynamic_cast follow the same rule during construction and destruction.|Calling a pure virtual function this way is undefined behavior and commonly aborts. Pass needed information to the base constructor as arguments, or use a factory that completes initialization after construction.',
     program('', r'''    Derived d;
    std::cout << "body sees " << d.kind() << "\n";''',
             r'''struct Base {
    Base() { std::cout << "ctor sees " << kind() << "\n"; }
    virtual ~Base() { std::cout << "dtor sees " << kind() << "\n"; }
    virtual const char* kind() const { return "Base"; }
};
struct Derived : Base { const char* kind() const override { return "Derived"; } };
'''),'ctor sees Base\nbody sees Derived\ndtor sees Base\n',
     ('Call kind() in main through a Base reference instead of the Derived object.', 'std::cout << "body sees " << d.kind()', 'const Base& b = d;\n    std::cout << "body sees " << b.kind()', 'ctor sees Base\nbody sees Derived\ndtor sees Base\n', 'After construction completes, the dynamic type is Derived, so dispatch through a base reference still reaches Derived::kind.'),
     'During Base\'s constructor, which kind() runs for an object whose complete type is Derived?', 'Base::kind, because the dynamic type is Base while Base is being constructed', ['Derived::kind, because the object is a Derived','It is always undefined behavior'],
     'Dispatch during construction uses the class whose constructor is executing.', 'class.cdtor',D)

unit(S,'non-virtual-interface','A non-virtual interface keeps policy in the base',14,
     'In the non-virtual interface idiom, the public functions are non-virtual and call private or protected virtual hooks. The base class owns the contract: argument checks, logging, locking, and postconditions run on every call no matter which derived class supplies the hook.|A derived class may override a private virtual function; access control governs who can call a name, not who can override it. Clients cannot bypass the wrapper by calling the hook directly.|The idiom adds a layer of indirection and works best when the wrapper has real policy to enforce. Keep the hooks narrow and document which preconditions the base already established before calling them.',
     program('cctype string', r'''    Upper upper;
    const Encoder& e = upper;
    std::cout << e.encode("ab") << " " << e.encode("") << "\n";''',
             r'''class Encoder {
public:
    virtual ~Encoder() = default;
    std::string encode(const std::string& input) const {
        if (input.empty()) return "<empty>";
        return "[" + do_encode(input) + "]";
    }
private:
    virtual std::string do_encode(const std::string& input) const = 0;
};
class Upper : public Encoder {
    std::string do_encode(const std::string& input) const override {
        std::string out = input;
        for (char& c : out) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        return out;
    }
};
'''),'[AB] <empty>\n',
     ('Change the framing policy in the base wrapper only.', '"[" + do_encode(input) + "]"', '"<" + do_encode(input) + ">"', '<AB> <empty>\n', 'The policy lives in one non-virtual function, so every encoder picks up the new framing without changing derived classes.'),
     'Can a derived class override a private virtual function of its base?', 'Yes; access controls calling a name, not overriding it', ['No; private virtual functions cannot be overridden','Only if the derived class is declared a friend'],
     'Overriding is about matching signatures; access checks apply at the point of a call.', 'class.virtual',D)

unit(S,'access-per-class','Access control is per class, and friendship is granted explicitly',14,
     'private and protected restrict which code may name a member. The check is per class, not per object: a member function of Account may read the private balance of any Account, which is how copy constructors and comparison functions work.|A friend declaration grants one function or class access to the private members of the declaring class. Friendship is not inherited, not transitive, and not reciprocal. Protected members of a base may be accessed by a derived class only through objects of that derived type.|Access control is a compile-time aid for keeping invariants, not a security boundary. Every friend widens the set of code that must preserve the invariants, so grant it narrowly.',
     program('', r'''    Account a(50), b(20);
    std::cout << a.richer_than(b) << " " << Auditor::peek(b) << "\n";''',
             r'''class Account {
    int balance_;
    friend class Auditor;
public:
    explicit Account(int b) : balance_(b) {}
    bool richer_than(const Account& other) const { return balance_ > other.balance_; }
};
class Auditor { public: static int peek(const Account& a) { return a.balance_; } };
'''),'1 20\n',
     ('Give account a the smaller balance.', 'Account a(50), b(20);', 'Account a(10), b(20);', '0 20\n', 'richer_than still reads other.balance_ legally; only the compared values changed.'),
     'Can richer_than read other.balance_ of a different Account object?', 'Yes; access is checked per class, not per object', ['No; private members are visible only through this','Only if other is declared a friend'],
     'Member functions of a class can access private members of any object of that class.', 'class.access',D)

# Drills: stage 03
drill('raii','Predict output','Early return still unwinds locals',
      M(r'''    f(true);
    std::cout << "|";
    f(false);''', 'iostream', r'''struct Guard { const char* name; ~Guard() { std::cout << name; } };
int f(bool early) { Guard a{"a"}; if (early) return 1; Guard b{"b"}; return 2; }'''),
      'What does this print?', 'a|ba', ['a|ab', '|ba'],
      'Only constructed locals are destroyed, in reverse order of construction. The early return leaves before b exists; the full path destroys b then a.')
drill('raii','Predict output','Exceptions unwind before the handler runs',
      M(r'''    try { Guard g{"g"}; throw 1; }
    catch (int) { std::cout << "c"; }''', 'iostream', r'''struct Guard { const char* name; ~Guard() { std::cout << name; } };'''),
      'What does this print?', 'gc', ['cg', 'c'],
      'Stack unwinding destroys g when control leaves the try block, before the matching handler executes.')
drill('raii','Predict output','A throwing constructor and its members',
      M(r'''    try { Whole w; }
    catch (int) { std::cout << "!"; }''', 'iostream', r'''struct Member { ~Member() { std::cout << "m"; } };
struct Whole { Member m; Whole() { throw 1; } ~Whole() { std::cout << "w"; } };'''),
      'What does this print?', 'm!', ['wm!', '!'],
      'An object whose constructor throws never finished construction, so its destructor does not run; already constructed members are destroyed.')

drill('unique-ownership','Compiles?','Copying a unique_ptr',
      M(r'''    auto p = std::make_unique<int>(1);
    auto q = p;
    (void)q;''', 'memory'),
      'Does this program compile?', 'No: unique_ptr has no copy constructor', ['Yes; q shares ownership with p', 'Yes; p becomes null after the copy'],
      'unique_ptr is move-only. Transfer ownership with std::move(p).', check='reject', diagnostic='deleted copy constructor')
drill('unique-ownership','Predict output','release gives up ownership without deleting',
      M(r'''    std::unique_ptr<int> p(new int(4));
    int* raw = p.release();
    std::cout << (p == nullptr) << *raw << "\n";
    delete raw;''', 'iostream memory'),
      'What does this print?', '14', ['04', '1 then a crash'],
      'release returns the pointer and sets p to null without destroying the object, so the caller must delete it.')
drill('unique-ownership','Undefined behavior','Two owners from one raw pointer',
      M(r'''    int* raw = new int(1);
    std::unique_ptr<int> a(raw);
    std::unique_ptr<int> b(raw);''', 'memory'),
      'What happens at the end of main?', 'Both unique_ptrs delete the same pointer: a double free', ['The second unique_ptr detects the first and does nothing', 'It leaks the integer'],
      'Each unique_ptr assumes sole ownership. Constructing two from one raw pointer gives two deletes.', check='asan')

drill('shared-and-weak','Predict output','weak_ptr does not add to use_count',
      M(r'''    auto a = std::make_shared<int>(1);
    auto b = a;
    std::weak_ptr<int> w = a;
    std::cout << a.use_count() << "\n";''', 'iostream memory'),
      'What does this print?', '2', ['3', '1'],
      'use_count counts shared owners only. A weak_ptr increments the separate weak count.')
drill('shared-and-weak','Predict output','A shared_ptr cycle never destroys',
      M(r'''    {
        auto x = std::make_shared<Node>();
        auto y = std::make_shared<Node>();
        x->next = y;
        y->next = x;
    }
    std::cout << "end\n";''', 'iostream memory', r'''struct Node { std::shared_ptr<Node> next; ~Node() { std::cout << "~"; } };'''),
      'What does this print?', 'end', ['~~end', '~end'],
      'Each node keeps the other\'s count at one after the locals go away, so neither destructor runs. One edge should be a weak_ptr.')
drill('shared-and-weak','Predict output','expired after the last owner leaves',
      M(r'''    std::weak_ptr<int> w;
    {
        auto s = std::make_shared<int>(3);
        w = s;
        std::cout << w.expired();
    }
    std::cout << w.expired() << "\n";''', 'iostream memory'),
      'What does this print?', '01', ['00', '11'],
      'The weak_ptr observes the object without owning it; once s is destroyed, no strong owner remains.')

drill('rule-of-zero','Predict output','Member values give deep copies for free',
      M(r'''    Doc a{"x", {1}};
    Doc b = a;
    b.title += "y";
    b.pages.push_back(2);
    std::cout << a.title << a.pages.size() << " " << b.title << b.pages.size() << "\n";''', 'iostream string vector', r'''struct Doc { std::string title; std::vector<int> pages; };'''),
      'What does this print?', 'x1 xy2', ['xy2 xy2', 'x1 xy1'],
      'The implicit copy constructor copies each member, and std::string and std::vector copy their contents.')
drill('rule-of-zero','Undefined behavior','Destructor without copy control',
      M(r'''    {
        Buf a;
        Buf b = a;
    }''', 'iostream', r'''struct Buf { int* p; Buf() : p(new int(1)) {} ~Buf() { delete p; } };'''),
      'What goes wrong at the closing brace?', 'Both objects delete the same pointer: a double free', ['Nothing; the implicit copy allocates a new int', 'Only a memory leak'],
      'The implicit copy constructor copies the pointer value. Use unique_ptr or vector and the problem disappears.', check='asan')
drill('rule-of-zero','Compiles?','A unique_ptr member makes the class move-only',
      M(r'''    Owner a;
    Owner b = a;
    (void)b;''', 'memory', r'''struct Owner { std::unique_ptr<int> p; };'''),
      'Does this program compile?', 'No: Owner\'s implicit copy constructor is deleted', ['Yes; the pointer is shared', 'Yes; the copy leaves a.p null'],
      'An implicit copy constructor is defined as deleted when a member cannot be copied.', check='reject', diagnostic='implicitly-deleted copy constructor')

drill('move-semantics','Copies and moves','std::move on a const object',
      M(r'''    const P a;
    P b = std::move(a);
    (void)b;''', 'iostream utility', r'''struct P { P() {} P(const P&) { std::cout << "copy\n"; } P(P&&) { std::cout << "move\n"; } };'''),
      'What does this print?', 'copy', ['move', 'It does not compile'],
      'std::move(a) has type const P&&, which cannot bind to P&&, so the const P& copy constructor is chosen.')
drill('move-semantics','Predict output','A named rvalue reference is an lvalue',
      M(r'''    g(P{});
    std::cout << "\n";''', 'iostream utility', r'''struct P {};
void f(P&&) { std::cout << "rv"; }
void f(const P&) { std::cout << "lv"; }
void g(P&& x) { f(x); f(std::move(x)); }'''),
      'What does this print?', 'lvrv', ['rvrv', 'lvlv'],
      'The expression x is an lvalue even though its declared type is P&&; only std::move(x) is an xvalue.')
drill('move-semantics','Copies and moves','return std::move blocks elision',
      M(r'''    P q = make();
    (void)q;''', 'iostream utility', r'''struct P { P() {} P(const P&) { std::cout << "copy\n"; } P(P&&) { std::cout << "move\n"; } };
P make() { P p; return std::move(p); }'''),
      'Compiled as C++17, what does this print?', 'move', ['Nothing is printed', 'copy'],
      'return std::move(p) returns an xvalue, which is not eligible for named return value elision, so one move happens. Initializing q from the prvalue make() is guaranteed elision.', standard=17)

drill('forwarding','Predict output','Deduction for T&&',
      M(r'''    int x = 0;
    f(x);
    f(1);
    std::cout << "\n";''', 'iostream type_traits', r'''template<class T> void f(T&&) { std::cout << std::is_lvalue_reference<T>::value; }'''),
      'What does this print?', '10', ['00', '11'],
      'For an lvalue argument a forwarding reference deduces T as int&; for an rvalue it deduces int.')
drill('forwarding','Predict output','forward preserves the argument category',
      M(r'''    int x = 0;
    sink(x);
    sink(std::move(x));
    std::cout << "\n";''', 'iostream utility', r'''void use(int&) { std::cout << "L"; }
void use(int&&) { std::cout << "R"; }
template<class T> void sink(T&& v) { use(std::forward<T>(v)); }'''),
      'What does this print?', 'LR', ['LL', 'RR'],
      'std::forward<T> casts back to an rvalue only when T was deduced as a non-reference, i.e. from an rvalue argument.')
drill('forwarding','Compiles?','vector<T>&& is not a forwarding reference',
      M(r'''    std::vector<int> v{1};
    take(v);''', 'vector', r'''template<class T> void take(std::vector<T>&&) {}'''),
      'Does this program compile?', 'No: std::vector<T>&& is an rvalue reference and cannot bind the lvalue v', ['Yes; T&& in any template is a forwarding reference', 'Yes; v is moved implicitly'],
      'Only a parameter of the exact form T&& for a deduced template parameter T is a forwarding reference.', check='reject', diagnostic='no matching function')

drill('exception-guarantees','Predict output','A partial update survives the exception',
      M(r'''    std::vector<int> v;
    try { bad(v); } catch (int) {}
    std::cout << v.size() << "\n";''', 'iostream vector', r'''void bad(std::vector<int>& v) { v.push_back(1); throw 1; }'''),
      'What does this print?', '1', ['0', '2'],
      'Nothing rolls back the push_back. bad gives only the basic guarantee; commit-after-prepare would be needed for the strong one.')
drill('exception-guarantees','Predict output','at() checks before writing',
      M(r'''    std::vector<int> v{1, 2};
    try { v.at(5) = 3; } catch (const std::out_of_range&) { std::cout << "range "; }
    std::cout << v.size() << "\n";''', 'iostream stdexcept vector'),
      'What does this print?', 'range 2', ['range 6', '2'],
      'at throws out_of_range before any element is touched, so the vector is unchanged.')
drill('exception-guarantees','Concept','A throwing destructor',
      '', 'A destructor is implicitly noexcept. What happens if an exception escapes it?', 'std::terminate is called', ['The exception propagates to the caller normally', 'The exception is silently discarded'],
      'Since C++11 destructors are noexcept unless declared otherwise, and an exception leaving a noexcept function calls std::terminate.', check='reasoning')

drill('destruction-order','Predict output','Members are destroyed in reverse declaration order',
      M(r'''    { Pair s; }
    std::cout << "\n";''', 'iostream', r'''struct P { char c; ~P() { std::cout << c; } };
struct Pair { P a{'a'}; P b{'b'}; };'''),
      'What does this print?', 'ba', ['ab', 'aabb'],
      'Members are constructed in declaration order and destroyed in the reverse order.')
drill('destruction-order','Predict output','The initializer list order does not matter',
      M(r'''    S s;
    std::cout << "\n";''', 'iostream', r'''struct L { L(char c) { std::cout << c; } };
struct S { L x; L y; S() : y('y'), x('x') {} };'''),
      'What does this print?', 'xy', ['yx', 'It does not compile'],
      'Members are always initialized in declaration order; compilers warn (-Wreorder) when the list is written differently.')
drill('destruction-order','Predict output','Base, member, body, and back',
      M(r'''    { Derived d; }
    std::cout << "\n";''', 'iostream', r'''struct B { B() { std::cout << "B"; } ~B() { std::cout << "~B"; } };
struct M { M() { std::cout << "M"; } ~M() { std::cout << "~M"; } };
struct Derived : B { M m; Derived() { std::cout << "D"; } ~Derived() { std::cout << "~D"; } };'''),
      'What does this print?', 'BMD~D~M~B', ['MBD~D~B~M', 'BMD~B~M~D'],
      'Bases are constructed before members, members before the constructor body; destruction exactly reverses that.')

drill('nonowning-views','Undefined behavior','A view of a temporary string',
      M(r'''    std::string_view v = std::string("a long string that certainly needs heap storage");
    std::cout << v << "\n";''', 'iostream string string_view'),
      'What is wrong with this program?', 'The view reads a string freed at the end of its declaration', ['Nothing; string_view extends the temporary', 'It fails to compile because string_view cannot bind a temporary'],
      'The temporary std::string is destroyed at the end of the full-expression; string_view stores only a pointer and a length.', check='asan')
drill('nonowning-views','Predict output','remove_prefix moves the view',
      M(r'''    std::string_view v = "hello world";
    v.remove_prefix(6);
    std::cout << v << v.size() << "\n";''', 'iostream string_view'),
      'What does this print?', 'world5', ['hello world11', 'world11'],
      'remove_prefix advances the start and shrinks the length; it never modifies the characters.')
drill('nonowning-views','Predict output','A view is not null-terminated',
      M(r'''    std::string_view v = std::string_view("abcdef").substr(0, 3);
    std::cout << v.size() << " " << std::strlen(v.data()) << "\n";''', 'iostream cstring string_view'),
      'What does this print?', '3 6', ['3 3', '6 6'],
      'substr narrows the length but data() still points into the original literal, whose terminator is after f. Never pass view.data() to a C-string API.')

drill('iterator-invalidation','Predict output','reserve keeps a pointer valid',
      M(r'''    std::vector<int> v;
    v.reserve(4);
    v.push_back(1);
    int* p = &v[0];
    v.push_back(2);
    std::cout << (p == &v[0]) << "\n";''', 'iostream vector'),
      'What does this print?', '1', ['0', 'It is undefined behavior'],
      'push_back invalidates pointers only when size would exceed capacity. With room reserved, no reallocation occurs.')
drill('iterator-invalidation','Undefined behavior','A reference across push_back',
      M(r'''    std::vector<int> v{1};
    int& r = v[0];
    v.push_back(2);
    std::cout << r << "\n";''', 'iostream vector'),
      'What is wrong with this program?', 'push_back reallocates, so r refers to freed storage', ['Nothing; references into a vector track reallocation', 'r now refers to the new last element'],
      'A vector built from one element has capacity one here; growth moves elements and frees the old buffer.', check='asan')
drill('iterator-invalidation','Predict output','erase returns the next valid iterator',
      M(r'''    std::vector<int> v{1, 2, 3, 4, 5};
    for (auto it = v.begin(); it != v.end();) {
        if (*it % 2 == 0) it = v.erase(it); else ++it;
    }
    for (int x : v) std::cout << x;
    std::cout << "\n";''', 'iostream vector'),
      'What does this print?', '135', ['1345', '24'],
      'Using erase\'s return value continues with the element after the erased one, so no element is skipped.')

drill('initializer-list-selection','Predict output','Parentheses versus braces for one integer',
      M(r'''    std::vector<int> a(2), b{2};
    std::cout << a.size() << b.size() << "\n";''', 'iostream vector'),
      'What does this print?', '21', ['22', '12'],
      'a(2) uses the count constructor; b{2} prefers the initializer_list constructor and holds the single value 2.')
drill('initializer-list-selection','Predict output','A string from three and x',
      M(r'''    std::string s(3, 'x');
    std::string t{3, 'x'};
    std::cout << s.size() << t.size() << "\n";''', 'iostream string'),
      'What does this print?', '32', ['33', '23'],
      'Braces select the initializer_list<char> constructor, so t holds two characters: the value 3 and x.')
drill('initializer-list-selection','Predict output','auto with braces',
      M(r'''    auto x{5};
    auto y = {5};
    std::cout << std::is_same<decltype(x), int>::value << std::is_same<decltype(y), std::initializer_list<int>>::value << "\n";''', 'iostream initializer_list type_traits'),
      'Compiled as C++17, what does this print?', '11', ['01', '10'],
      'Direct-list-initialization with one element deduces the element type; copy-list-initialization with = deduces initializer_list.', standard=17)

drill('guaranteed-elision','Compiles?','Returning a prvalue of a non-movable type in C++17',
      M(r'''    NoMove n = make();
    (void)n;''', 'iostream', r'''struct NoMove { NoMove() = default; NoMove(const NoMove&) = delete; NoMove(NoMove&&) = delete; };
NoMove make() { return NoMove{}; }'''),
      'Compiled as C++17, does this program compile and run?', 'Yes: prvalues initialize the result object directly, so no move constructor is needed', ['No: returning by value needs a move constructor', 'Only with optimization enabled'],
      'C++17 guarantees that a prvalue initializes its destination without a temporary.', check='compiles')
drill('guaranteed-elision','Compiles?','The same code in C++14',
      M(r'''    NoMove n = make();
    (void)n;''', 'iostream', r'''struct NoMove { NoMove() = default; NoMove(const NoMove&) = delete; NoMove(NoMove&&) = delete; };
NoMove make() { return NoMove{}; }'''),
      'Compiled as C++14, does this program compile?', 'No: C++14 requires an accessible move or copy constructor even when the copy is elided', ['Yes; elision always applied', 'Yes, but it prints a warning only'],
      'Before C++17, elision was an optional optimization and the constructor it skipped still had to be usable.', check='reject', diagnostic='deleted constructor', standard=14)
drill('guaranteed-elision','Copies and moves','Returning a by-value parameter',
      M(r'''    P a;
    P b = pass(a);
    (void)b;
    std::cout << "\n";''', 'iostream', r'''struct P { P() {} P(const P&) { std::cout << "C"; } P(P&&) { std::cout << "M"; } };
P pass(P p) { return p; }'''),
      'Compiled as C++17, what does this print?', 'CM', ['C', 'CC'],
      'The argument is copied into the parameter. A parameter is not eligible for return elision but is implicitly moved; b is initialized from the prvalue without another operation.', standard=17)

drill('reference-qualified-members','Predict output','A temporary receiver selects &&',
      M(r'''    Box b;
    std::cout << Box{}.category() << b.category() << "\n";''', 'iostream', r'''struct Box { const char* category() & { return "borrow"; } const char* category() && { return "consume"; } };'''),
      'What does this print?', 'consumeborrow', ['borrowborrow', 'consumeconsume'],
      'Box{} is a prvalue object expression, so the &&-qualified overload is chosen; b is an lvalue.')
drill('reference-qualified-members','Compiles?','Only an & overload on a temporary',
      M(r'''    return V{}.get();''', 'iostream', r'''struct V { int get() & { return 1; } };'''),
      'Does this program compile?', 'No: a non-const &-qualified member cannot be called on an rvalue', ['Yes; the temporary binds to the implicit object parameter', 'Yes, and main returns 1'],
      'A non-const & qualifier requires an lvalue object expression.', check='reject', diagnostic='ref-qualifier')
drill('reference-qualified-members','Predict output','const& accepts rvalues',
      M(r'''    std::cout << C{}.f() << "\n";''', 'iostream', r'''struct C { const char* f() const& { return "const&"; } };'''),
      'What does this print?', 'const&', ['It does not compile', 'An empty line'],
      'Like a const T& parameter, a const& implicit object parameter can bind an rvalue when no && overload exists.')

drill('value-categories-decltype','Predict output','decltype with and without parentheses',
      M(r'''    int x = 0;
    std::cout << std::is_same<decltype(x), int>::value << std::is_same<decltype((x)), int&>::value << "\n";''', 'iostream type_traits'),
      'What does this print?', '11', ['10', '01'],
      'decltype(x) names the declared type int; decltype((x)) applies the expression rule and gives int& for an lvalue.')
drill('value-categories-decltype','Predict output','String literals and std::move',
      M(r'''    int x = 0;
    std::cout << std::is_rvalue_reference<decltype(std::move(x))>::value
              << std::is_lvalue_reference<decltype(("abc"))>::value << "\n";''', 'iostream type_traits utility'),
      'What does this print?', '11', ['10', '01'],
      'std::move(x) is an xvalue of type int&&. A string literal is an lvalue of array type, so decltype gives const char(&)[4].')
drill('value-categories-decltype','Compiles?','Binding a prvalue to int&',
      M(r'''    int& r = 5;
    (void)r;'''),
      'Does this program compile?', 'No: a non-const lvalue reference cannot bind to a prvalue', ['Yes; a temporary int is created and extended', 'Yes, but r is dangling'],
      'Only const lvalue references and rvalue references may bind to temporaries.', check='reject', diagnostic='non-const lvalue reference')

drill('temporary-lifetime-extension','Undefined behavior','A getter on a temporary',
      M(r'''    const std::string& r = H{"a long string that certainly needs heap storage"}.get();
    std::cout << r << "\n";''', 'iostream string', r'''struct H { std::string s; const std::string& get() const { return s; } };'''),
      'What is wrong with this program?', 'The temporary H is destroyed at the semicolon, so r dangles', ['Nothing; const references extend temporaries', 'It fails to compile'],
      'Extension applies only when a reference binds directly to the temporary or its member, not through a returned reference.', check='asan')
drill('temporary-lifetime-extension','Predict output','When an extended temporary dies',
      M(r'''    {
        const T& r = T{};
        (void)r;
        std::cout << "body";
    }
    std::cout << "end\n";''', 'iostream', r'''struct T { ~T() { std::cout << "~"; } };'''),
      'What does this print?', 'body~end', ['~bodyend', 'bodyend~'],
      'The extended temporary lives until r goes out of scope at the closing brace.')
drill('temporary-lifetime-extension','Predict output','An unbound temporary lives to the end of the full-expression',
      M(r'''    std::cout << T{5}.v << "|";
    std::cout << "\n";''', 'iostream', r'''struct T { int v; ~T() { std::cout << "~"; } };'''),
      'What does this print?', '5|~', ['5~|', '~5|'],
      'The temporary is destroyed at the end of the whole statement, after both insertions.')

drill('rule-of-five','Copies and moves','What std::swap costs',
      M(r'''    P a, b;
    std::swap(a, b);
    std::cout << "\n";''', 'iostream utility', r'''struct P {
    P() = default;
    P(const P&) { std::cout << "C"; }
    P(P&&) noexcept { std::cout << "M"; }
    P& operator=(const P&) { std::cout << "c="; return *this; }
    P& operator=(P&&) noexcept { std::cout << "m="; return *this; }
};'''),
      'What does this print?', 'Mm=m=', ['CC=c=', 'Mm='],
      'The generic swap move-constructs a temporary from a, then move-assigns a from b and b from the temporary.')
drill('rule-of-five','Compiles?','A defaulted move constructor and copying',
      M(r'''    S a;
    S b = a;
    (void)b;''', 'iostream', r'''struct S { S() = default; S(S&&) = default; };'''),
      'Does this program compile?', 'No: declaring a move constructor deletes the implicit copy constructor', ['Yes; the copy constructor is still implicit', 'Yes; the move constructor is used for lvalues'],
      'A user-declared move operation causes the implicit copy operations to be defined as deleted.', check='reject', diagnostic='implicitly-deleted copy constructor')
drill('rule-of-five','Undefined behavior','Copy assignment that deletes first',
      M(r'''    Buf a;
    Buf& alias = a;
    a = alias;
    std::cout << *a.p << "\n";''', 'iostream', r'''struct Buf {
    int* p;
    Buf() : p(new int(1)) {}
    Buf(const Buf&) = delete;
    ~Buf() { delete p; }
    Buf& operator=(const Buf& o) { delete p; p = new int(*o.p); return *this; }
};'''),
      'What is the bug?', 'Self-assignment reads *o.p after deleting it', ['None; the new int replaces the old one', 'The copy constructor is deleted, so it does not compile'],
      'When o is *this, delete p frees the value that new int(*o.p) then reads. Allocate first or use copy-and-swap.', check='asan')

drill('copy-and-swap','Copies and moves','One by-value assignment for every source',
      M(r'''    W a, b;
    a = b;
    a = std::move(b);
    a = W{};
    std::cout << "\n";''', 'iostream utility', r'''struct W {
    W() = default;
    W(const W&) { std::cout << "C"; }
    W(W&&) noexcept { std::cout << "M"; }
    W& operator=(W) noexcept { std::cout << "A"; return *this; }
};'''),
      'Compiled as C++17, what does this print?', 'CAMAA', ['CAMAMA', 'AAA'],
      'The parameter is copy-constructed from an lvalue, move-constructed from an xvalue, and initialized directly from a prvalue.', standard=17)
drill('copy-and-swap','Concept','The cost of copy-and-swap',
      '', 'Compared with a hand-written assignment that reuses existing storage, what does copy-and-swap give up?', 'It always builds a new representation, so it cannot reuse the target\'s capacity', ['It loses the strong exception guarantee', 'It makes self-assignment undefined'],
      'The by-value parameter is a complete new copy. That buys strong safety at the cost of an allocation even when the target already had room.', check='reasoning')
drill('copy-and-swap','Predict output','noexcept of a by-value assignment',
      M(r'''    std::cout << std::is_nothrow_move_assignable<N>::value << std::is_nothrow_copy_assignable<N>::value << "\n";''', 'iostream type_traits vector', r'''struct N {
    std::vector<int> v;
    N() = default;
    N(const N&) = default;
    N(N&&) noexcept = default;
    N& operator=(N o) noexcept { v.swap(o.v); return *this; }
};'''),
      'What does this print?', '10', ['11', '00'],
      'The trait checks the whole assignment expression, including constructing the parameter. Moving is noexcept; copying a vector may throw.')

drill('placement-new-launder','Predict output','Storage scope does not destroy the object',
      M(r'''    {
        alignas(T) unsigned char buf[sizeof(T)];
        new (buf) T;
    }
    std::cout << "end\n";''', 'iostream new', r'''struct T { ~T() { std::cout << "~"; } };'''),
      'What does this print?', 'end', ['~end', 'end~'],
      'The byte array\'s lifetime ends without running T\'s destructor. The program had to call it explicitly.')
drill('placement-new-launder','Concept','When std::launder is needed',
      '', 'When is std::launder needed after placement new into existing storage?', 'When you reach the new object through a pointer that pointed to the old storage or object, such as a reinterpret_cast of the buffer', ['After every placement new, even when using the pointer it returned', 'Never; it only affects optimization flags'],
      'The pointer returned by placement new already points to the new object. A pointer derived from the old storage does not, and launder obtains one that does.', check='reasoning')
drill('placement-new-launder','Undefined behavior','Misaligned placement',
      M(r'''    alignas(int) unsigned char buf[8];
    int* p = new (buf + 1) int(5);
    return *p == 5 ? 0 : 1;''', 'new'),
      'What is wrong with this program?', 'buf + 1 is not suitably aligned for int', ['Nothing; placement new aligns the address', 'The buffer is too small'],
      'Placement new uses exactly the address it is given. Constructing an int at an odd address violates its alignment requirement.', check='ubsan')

drill('new-delete-pairing','Undefined behavior','delete on an array of class type',
      M(r'''    T* p = new T[3];
    delete p;''', 'iostream', r'''struct T { ~T() {} int x; };'''),
      'What happens?', 'Undefined behavior: the pointer from new[] is passed to the single-object delete', ['Only the first element is destroyed, which is valid', 'All three elements are destroyed correctly'],
      'With a nontrivial destructor, the implementation stores a count before the array, so delete receives an address that was never allocated.', check='asan')
drill('new-delete-pairing','Predict output','delete[] destroys in reverse order',
      M(r'''    T* p = new T[3]{{1}, {2}, {3}};
    delete[] p;
    std::cout << "\n";''', 'iostream', r'''struct T { int id; ~T() { std::cout << id; } };'''),
      'What does this print?', '321', ['123', '3'],
      'Array elements are destroyed in reverse order of construction.')
drill('new-delete-pairing','Undefined behavior','Deleting twice',
      M(r'''    int* p = new int(1);
    delete p;
    delete p;'''),
      'What happens?', 'A double free: undefined behavior', ['The second delete is ignored', 'The second delete frees a fresh allocation'],
      'delete does not set the pointer to null. Owning handles prevent this whole class of error.', check='asan')

drill('noexcept-move-growth','Predict output','Which moves are noexcept?',
      M(r'''    std::cout << std::is_nothrow_move_constructible<A>::value << std::is_nothrow_move_constructible<B>::value << "\n";''', 'iostream string type_traits', r'''struct A { A() = default; A(A&&) {} };
struct B { std::string s; };'''),
      'What does this print?', '01', ['11', '10'],
      'A user-written move constructor without noexcept is potentially throwing. B\'s implicit move is noexcept because std::string\'s move constructor is.')
drill('noexcept-move-growth','Copies and moves','A move-only type with a throwing move',
      M(r'''    std::vector<O> v;
    v.reserve(1);
    v.emplace_back();
    v.emplace_back();
    std::cout << "\n";''', 'iostream vector', r'''struct O { O() = default; O(const O&) = delete; O(O&&) { std::cout << "m"; } };'''),
      'What does this print?', 'm', ['Nothing is printed', 'It does not compile'],
      'With no copy constructor available, move_if_noexcept still moves; the strong guarantee is then lost if the move throws.')
drill('noexcept-move-growth','Copies and moves','An implicit move inherits a member\'s noexcept',
      M(r'''    std::vector<H> v;
    v.reserve(1);
    v.emplace_back();
    v.emplace_back();
    std::cout << "copies " << Item::copies << "\n";''', 'iostream vector', r'''struct Item { static int copies; Item() = default; Item(const Item&) { ++copies; } Item(Item&&) {} };
int Item::copies = 0;
struct H { Item i; };'''),
      'What does this print?', 'copies 1', ['copies 0', 'copies 2'],
      'H\'s implicit move constructor is noexcept only if Item\'s is. It is not, so growth copies the existing H.')

drill('shared-from-this','Predict output','shared_from_this without an owner',
      M(r'''    Session s;
    try { s.self(); } catch (const std::bad_weak_ptr&) { std::cout << "bad_weak_ptr"; }
    std::cout << "\n";''', 'iostream memory', r'''struct Session : std::enable_shared_from_this<Session> {
    std::shared_ptr<Session> self() { return shared_from_this(); }
};'''),
      'Compiled as C++17, what does this print?', 'bad_weak_ptr', ['Nothing is printed', 'It crashes with a double free'],
      'Since C++17, shared_from_this throws std::bad_weak_ptr when no shared_ptr owns the object.', standard=17)
drill('shared-from-this','Undefined behavior','shared_ptr built from this',
      M(r'''    auto a = std::shared_ptr<S>(new S);
    auto b = a->self();''', 'memory', r'''struct S { std::shared_ptr<S> self() { return std::shared_ptr<S>(this); } };'''),
      'What happens at the end of main?', 'Two independent control blocks both delete the object', ['b joins a\'s ownership group', 'The object leaks'],
      'Only shared_from_this finds the existing control block. A new shared_ptr from a raw pointer always starts a new one.', check='asan')
drill('shared-from-this','Predict output','The object dies before its weak_ptr',
      M(r'''    std::weak_ptr<T> w;
    {
        auto s = std::make_shared<T>();
        w = s;
    }
    std::cout << "|" << w.expired() << "\n";''', 'iostream memory', r'''struct T { ~T() { std::cout << "~"; } };'''),
      'What does this print?', '~|1', ['|1~', '|0'],
      'The object is destroyed when the last shared owner goes; the control block (and with make_shared, its storage) waits only for the weak count.')

drill('moved-from-state','Undefined behavior','Reading a moved-from string',
      M(r'''    std::string s = "x";
    std::string t = std::move(s);
    std::cout << s.size() << t << "\n";''', 'iostream string utility'),
      'Does this program have undefined behavior?', 'No: s is valid but unspecified, so calling size() is allowed', ['Yes: any use of a moved-from object is undefined', 'Yes: s was freed by the move'],
      'size() has no precondition. The printed number is unspecified, which is different from undefined.', check='compiles')
drill('moved-from-state','Undefined behavior','Dereferencing a moved-from unique_ptr',
      M(r'''    auto p = std::make_unique<int>(1);
    auto q = std::move(p);
    std::cout << *p << "\n";''', 'iostream memory utility'),
      'What is wrong with this program?', 'A moved-from unique_ptr is specified to be null, so *p dereferences null', ['Nothing; p still points at the integer', 'It is a use-after-free of q\'s integer'],
      'unique_ptr documents its moved-from state exactly. The precondition of operator* is violated.', check='asan')
drill('moved-from-state','Predict output','A moved-from shared_ptr',
      M(r'''    auto a = std::make_shared<int>(1);
    auto b = std::move(a);
    std::cout << a.use_count() << b.use_count() << "\n";''', 'iostream memory utility'),
      'What does this print?', '01', ['11', '02'],
      'Moving a shared_ptr transfers ownership without touching the count; the source becomes empty.')

drill('dangling-temporaries','Undefined behavior','Range-for over a member of a temporary',
      M(r'''    for (int x : make().items()) std::cout << x;
    std::cout << "\n";''', 'iostream vector', r'''struct Box { std::vector<int> v; const std::vector<int>& items() const { return v; } };
Box make() { return Box{{1, 2, 3}}; }'''),
      'Compiled as C++17, what is wrong with this loop?', 'The temporary Box dies before the loop body runs, so the range dangles', ['Nothing; the range-init expression is lifetime-extended in full', 'It copies the vector, so it is merely slow'],
      'The hidden reference binds to the returned reference, not to the temporary Box. C++23 extends temporaries in the range initializer.', check='asan')
drill('dangling-temporaries','Undefined behavior','Keeping the result of std::max',
      M(r'''    const int& m = std::max(1, 2);
    std::cout << m << "\n";''', 'algorithm iostream'),
      'What is wrong with this program?', 'std::max returns a reference to a temporary argument that is destroyed at the semicolon', ['Nothing; the result is lifetime-extended', 'It returns a copy, so it is fine'],
      'std::max takes and returns const T&. The temporaries 1 and 2 die at the end of the full-expression.', check='asan')
drill('dangling-temporaries','Predict output','A view of a literal is safe',
      M(r'''    std::cout << name() << "\n";''', 'iostream string_view', r'''std::string_view name() { return "fixed"; }'''),
      'Is this safe, and what does it print?', 'fixed', ['It dangles and prints garbage', 'It does not compile'],
      'String literals have static storage duration, so a view returned from the function stays valid.')

# Drills: stage 04
drill('class-invariants','Predict output','A rejected constructor creates no object',
      M(r'''    try { Percent p(150); }
    catch (const std::invalid_argument& e) { std::cout << e.what(); }
    std::cout << "\n";''', 'iostream stdexcept', r'''struct Percent {
    int v;
    explicit Percent(int x) : v(x) { if (x < 0 || x > 100) throw std::invalid_argument("percent"); }
    ~Percent() { std::cout << "~"; }
};'''),
      'What does this print?', 'percent', ['~percent', 'percent~'],
      'A constructor that throws never completes, so no destructor runs for that object.')
drill('class-invariants','Code review','Public members and invariants',
      r'''#include <stdexcept>
struct Range {
    int lo, hi;
    Range(int a, int b) : lo(a), hi(b) { if (a > b) throw std::invalid_argument("range"); }
};
''',
      'What is the design flaw if Range must always satisfy lo <= hi?', 'Public data members let any caller break lo <= hi after construction', ['The constructor should return false instead of throwing', 'int cannot represent a range'],
      'An invariant can be maintained only if every mutation goes through code that checks it. Make the members private and offer checked operations.', check='reasoning')
drill('class-invariants','Compiles?','Copy-initialization and explicit',
      M(r'''    Percent p = 50;
    (void)p;''', 'iostream', r'''struct Percent { explicit Percent(int x) : v(x) {} int v; };'''),
      'Does this program compile?', 'No: copy-initialization cannot use an explicit constructor', ['Yes; 50 converts to Percent', 'Yes, but only with a warning'],
      'explicit constructors are considered only for direct-initialization and explicit casts.', check='reject', diagnostic='no viable conversion')

drill('aggregates','Predict output','Missing initializers are value-initialized',
      M(r'''    P p{1};
    std::cout << p.x << p.y << p.z << "\n";''', 'iostream', r'''struct P { int x; int y; int z; };'''),
      'What does this print?', '100', ['1 followed by indeterminate values', '111'],
      'Aggregate members without an explicit initializer are initialized from an empty initializer list, which zeroes ints.')
drill('aggregates','Predict output','Aggregates with base classes',
      M(r'''    D d{{1}, 2};
    std::cout << d.a << d.b << "\n";''', 'iostream', r'''struct B { int a; };
struct D : B { int b; };'''),
      'Compiled as C++17, what does this print?', '12', ['It does not compile', '02'],
      'Since C++17 a class with public non-virtual bases can be an aggregate, and the base is initialized first from its own brace list.')
drill('aggregates','Compiles?','A deleted default constructor in C++20',
      M(r'''    A a{};
    (void)a;''', 'iostream', r'''struct A { int x; A() = delete; };'''),
      'Compiled as C++20, does this program compile?', 'No: a user-declared constructor makes A a non-aggregate, so the deleted constructor is used', ['Yes; aggregate initialization bypasses the deleted constructor', 'Yes; x is zero-initialized'],
      'C++20 removed the loophole that let aggregate initialization ignore user-declared constructors. In C++17 this compiled.', check='reject', diagnostic='deleted constructor', standard=20)

drill('const-members','Compiles?','A non-const member on a const object',
      M(r'''    const Counter c{};
    c.bump();''', 'iostream', r'''struct Counter { int v = 0; void bump() { ++v; } };'''),
      'Does this program compile?', 'No: bump is not const, so it cannot be called on a const object', ['Yes; v is modified anyway', 'Yes; the call is ignored'],
      'The implicit object parameter of a non-const member is a non-const reference, which cannot bind a const object.', check='reject', diagnostic='not marked const')
drill('const-members','Predict output','A mutable cache in a const member',
      M(r'''    const C c{};
    c.get();
    c.get();
    std::cout << c.hits << "\n";''', 'iostream', r'''struct C { mutable int hits = 0; int get() const { ++hits; return 7; } };'''),
      'What does this print?', '2', ['0', 'It does not compile'],
      'mutable members may be modified through a const object. Use this only for state that is not part of the observable value.')
drill('const-members','Predict output','Overloading on const',
      M(r'''    V v;
    const V& cv = v;
    std::cout << v.at() << " " << cv.at() << "\n";''', 'iostream', r'''struct V { const char* at() const { return "const"; } const char* at() { return "mut"; } };'''),
      'What does this print?', 'mut const', ['const const', 'mut mut'],
      'Overload resolution chooses by the constness of the object expression.')

drill('inheritance-and-slicing','Predict output','By value versus by reference',
      M(r'''    B b;
    byval(b);
    byref(b);
    std::cout << "\n";''', 'iostream', r'''struct A { virtual ~A() = default; virtual const char* n() const { return "A"; } };
struct B : A { const char* n() const override { return "B"; } };
void byval(A a) { std::cout << a.n(); }
void byref(const A& a) { std::cout << a.n(); }'''),
      'What does this print?', 'AB', ['BB', 'AA'],
      'Passing by value copies only the A subobject into a new A. A reference preserves the dynamic type.')
drill('inheritance-and-slicing','Predict output','A vector of base objects',
      M(r'''    std::vector<A> v;
    v.push_back(B{});
    std::cout << v[0].n() << "\n";''', 'iostream vector', r'''struct A { virtual ~A() = default; virtual const char* n() const { return "A"; } };
struct B : A { const char* n() const override { return "B"; } };'''),
      'What does this print?', 'A', ['B', 'It does not compile'],
      'std::vector<A> stores A objects. The B argument is sliced when the element is constructed. Store unique_ptr<A> for polymorphism.')
drill('inheritance-and-slicing','Predict output','Assignment through a base reference',
      M(r'''    B b1, b2;
    b2.x = 5;
    b2.y = 6;
    A& r = b1;
    r = b2;
    std::cout << b1.x << b1.y << "\n";''', 'iostream', r'''struct A { int x = 1; };
struct B : A { int y = 2; };'''),
      'What does this print?', '52', ['56', '12'],
      'A::operator= copies only the A part, so b1 ends up with half of b2\'s state: partial assignment.')

drill('virtual-destruction','Predict output','Deleting through a base with a virtual destructor',
      M(r'''    Base* p = new Derived;
    delete p;
    std::cout << "\n";''', 'iostream', r'''struct Base { virtual ~Base() { std::cout << "~B"; } };
struct Derived : Base { ~Derived() override { std::cout << "~D"; } };'''),
      'What does this print?', '~D~B', ['~B', '~B~D'],
      'The virtual destructor dispatches to ~Derived, which then runs the base destructor.')
drill('virtual-destruction','Undefined behavior','No virtual destructor',
      r'''#include <string>
struct Base { ~Base() {} };
struct Derived : Base { std::string name = "x"; };
int main() { Base* p = new Derived; delete p; }
''',
      'What does the standard say about delete p?', 'Undefined behavior: deleting a Derived through a Base without a virtual destructor', ['Only ~Base runs, which is well defined', 'It is fine because Derived adds only a string'],
      'When the static and dynamic types differ, the static type must have a virtual destructor. In practice ~Derived is typically skipped and the string leaks, but no outcome is guaranteed.', check='reasoning')
drill('virtual-destruction','Compiles?','A protected non-virtual destructor',
      M(r'''    Base* p = new Derived;
    delete p;''', 'iostream', r'''struct Base { protected: ~Base() = default; };
struct Derived : Base {};'''),
      'Does this program compile?', 'No: the protected destructor forbids deletion through Base', ['Yes; protected members are accessible in main', 'Yes, but it leaks'],
      'A protected non-virtual base destructor is a deliberate design: it turns deletion through the base into a compile error.', check='reject', diagnostic='protected destructor')

drill('operator-design','Predict output','operator+ built from +=',
      M(r'''    Money a{5}, b{3};
    Money c = a + b;
    std::cout << a.cents << " " << c.cents << "\n";''', 'iostream', r'''struct Money {
    int cents;
    Money& operator+=(Money o) { cents += o.cents; return *this; }
};
Money operator+(Money a, Money b) { return a += b; }'''),
      'What does this print?', '5 8', ['8 8', '5 5'],
      'operator+ receives copies, so += modifies only the local parameter. The caller\'s a is unchanged.')
drill('operator-design','Predict output','Prefix and postfix increment',
      M(r'''    Counter c;
    std::cout << (c++).v << (++c).v << c.v << "\n";''', 'iostream', r'''struct Counter {
    int v = 0;
    Counter& operator++() { ++v; return *this; }
    Counter operator++(int) { Counter old = *this; ++v; return old; }
};'''),
      'Compiled as C++17, what does this print?', '022', ['012', '122'],
      'Postfix returns the old value; prefix returns the updated object. C++17 sequences the << operands left to right.', standard=17)
drill('operator-design','Compiles?','Overloading an operator for int',
      M(r'''    return 0;''', 'iostream', r'''int operator+(int a, int b) { return a - b; }'''),
      'Does this program compile?', 'No: an overloaded operator needs at least one class or enumeration parameter', ['Yes; it replaces built-in addition', 'Yes, but only in this translation unit'],
      'Built-in operators on fundamental types cannot be redefined.', check='reject', diagnostic='class or enumeration')

drill('casts-and-rtti','Predict output','dynamic_cast to a sibling type',
      M(r'''    A a;
    Base* p = &a;
    std::cout << (dynamic_cast<B*>(p) == nullptr) << (dynamic_cast<A*>(p) != nullptr) << "\n";''', 'iostream', r'''struct Base { virtual ~Base() = default; };
struct A : Base {};
struct B : Base {};'''),
      'What does this print?', '11', ['01', '10'],
      'A pointer dynamic_cast checks the dynamic type and returns null on failure.')
drill('casts-and-rtti','Predict output','dynamic_cast to a reference',
      M(r'''    A a;
    Base& r = a;
    try { B& b = dynamic_cast<B&>(r); (void)b; std::cout << "ok"; }
    catch (const std::bad_cast&) { std::cout << "bad_cast"; }
    std::cout << "\n";''', 'iostream typeinfo', r'''struct Base { virtual ~Base() = default; };
struct A : Base {};
struct B : Base {};'''),
      'What does this print?', 'bad_cast', ['ok', 'It is undefined behavior'],
      'References cannot be null, so a failed reference dynamic_cast throws std::bad_cast.')
drill('casts-and-rtti','Compiles?','dynamic_cast on a non-polymorphic base',
      M(r'''    Q q;
    P* p = &q;
    return dynamic_cast<Q*>(p) != nullptr;''', 'iostream', r'''struct P {};
struct Q : P {};'''),
      'Does this program compile?', 'No: a downcast with dynamic_cast needs a polymorphic source type', ['Yes, and it returns 1', 'Yes, and it returns 0'],
      'The run-time check relies on type information found through a virtual table, which P lacks.', check='reject', diagnostic='not polymorphic')

drill('type-erasure','Predict output','std::function stores a copy',
      M(r'''    int n = 0;
    auto counter = [n]() mutable { return ++n; };
    std::function<int()> f = counter;
    f();
    f();
    std::cout << counter() << "\n";''', 'functional iostream'),
      'What does this print?', '1', ['3', '0'],
      'std::function copied the lambda, including its captured n. Calls through f change only the copy.')
drill('type-erasure','Predict output','any_cast with the wrong type',
      M(r'''    std::any a = 5;
    try { long v = std::any_cast<long>(a); (void)v; std::cout << "long"; }
    catch (const std::bad_any_cast&) { std::cout << "bad"; }
    std::cout << "\n";''', 'any iostream'),
      'What does this print?', 'bad', ['long', '5'],
      'std::any checks the exact stored type; int does not convert to long through any_cast.', standard=17)
drill('type-erasure','Compiles?','A move-only lambda in std::function',
      M(r'''    std::function<void()> f = [p = std::make_unique<int>(1)] {};
    (void)f;''', 'functional memory'),
      'Does this program compile?', 'No: std::function requires a copy-constructible callable', ['Yes; std::function moves the lambda', 'Yes, but f cannot be copied later'],
      'std::function erases copying too, so it needs a copyable target. C++23 std::move_only_function lifts this.', check='reject', diagnostic='implicitly-deleted copy constructor')

drill('dependency-design','Predict output','A fake clock through an interface',
      M(r'''    FakeClock clock;
    Report report(clock);
    std::cout << report.stamp() << "\n";''', 'iostream string', r'''struct Clock { virtual ~Clock() = default; virtual int now() const = 0; };
struct FakeClock : Clock { int now() const override { return 42; } };
class Report {
    const Clock& clock_;
public:
    explicit Report(const Clock& c) : clock_(c) {}
    std::string stamp() const { return "t=" + std::to_string(clock_.now()); }
};'''),
      'What does this print?', 't=42', ['t=0', 'It does not compile'],
      'Report depends on the Clock interface, so a test can inject a deterministic implementation.')
drill('dependency-design','Predict output','A recording dependency',
      M(r'''    Recorder log;
    Service s(log);
    s.run();
    s.run();
    std::cout << log.count << "\n";''', 'iostream', r'''struct Logger { virtual ~Logger() = default; virtual void write(const char*) = 0; };
struct Recorder : Logger { int count = 0; void write(const char*) override { ++count; } };
struct Service { Logger& log; explicit Service(Logger& l) : log(l) {} void run() { log.write("run"); } };'''),
      'What does this print?', '2', ['0', '1'],
      'Service holds a reference to the injected logger, so both calls reach the same recorder.')
drill('dependency-design','Code review','A hard-wired clock',
      '', 'A class constructs a SystemClock member inside its constructor and reads it in every method. What is the main testing problem?', 'Tests cannot substitute a controllable clock without changing the class', ['SystemClock cannot be a member', 'The class becomes non-copyable'],
      'Creating the dependency internally fixes the choice. Injecting it through the constructor makes time controllable in tests.', check='reasoning')

drill('object-representation','Predict output','The first byte of an integer',
      M(r'''    std::uint32_t value = 0x01020304;
    unsigned char bytes[4];
    std::memcpy(bytes, &value, 4);
    std::cout << int(bytes[0]) << "\n";''', 'cstdint cstring iostream'),
      'On arm64 macOS, what does this print?', '4', ['1', '0'],
      'arm64 is little-endian, so the least significant byte is stored first. Byte order is a platform property.')
drill('object-representation','Predict output','The bits of 1.0f',
      M(r'''    float f = 1.0f;
    std::uint32_t bits;
    std::memcpy(&bits, &f, sizeof bits);
    std::cout << std::hex << bits << "\n";''', 'cstdint cstring iostream'),
      'With IEEE-754 binary32 floats, what does this print?', '3f800000', ['1', '00000001'],
      'memcpy copies the object representation without aliasing problems. 1.0 has exponent 127 and a zero fraction.')
drill('object-representation','Concept','Writing raw struct bytes',
      '', 'Why is writing a struct\'s raw bytes to a file not a portable serialization format?', 'Padding, byte order, and type sizes are ABI-specific', ['memcpy cannot copy structs', 'Files can store only text'],
      'Another compiler, architecture, or member order can produce different bytes for the same values. Encode each field explicitly.', check='reasoning')

drill('hidden-friends','Compiles?','Qualified lookup of a hidden friend',
      M(r'''    std::cout << ::twice(T{3}) << "\n";''', 'iostream', r'''struct T { int v; friend int twice(T t) { return t.v * 2; } };'''),
      'Does this program compile?', 'No: a hidden friend is not visible to qualified lookup', ['Yes, and it prints 6', 'Yes; friends are members of the enclosing namespace for all lookups'],
      'A friend first declared inside a class is found only by argument-dependent lookup.', check='reject', diagnostic='no member named')
drill('hidden-friends','Predict output','ADL finds the hidden friend',
      M(r'''    std::cout << twice(T{3}) << "\n";''', 'iostream', r'''struct T { int v; friend int twice(T t) { return t.v * 2; } };'''),
      'What does this print?', '6', ['3', 'It does not compile'],
      'The T argument makes T an associated class, so ADL finds its hidden friend.')
drill('hidden-friends','Compiles?','No conversion to reach a hidden friend',
      M(r'''    return twice(3);''', 'iostream', r'''struct T { T(int x) : v(x) {} int v; friend int twice(T t) { return t.v * 2; } };'''),
      'Does this program compile?', 'No: with an int argument, ADL has no reason to look inside T', ['Yes; 3 converts to T', 'Yes, and main returns 6'],
      'Hidden friends are found only when an argument already has the class as an associated type, which blocks surprising conversions.', check='reject', diagnostic='undeclared identifier')

drill('prototype-cloning','Predict output','Clone preserves the dynamic type',
      M(r'''    std::unique_ptr<Shape> original = std::make_unique<Circle>();
    auto copy = original->clone();
    std::cout << copy->name() << "\n";''', 'iostream memory', r'''struct Shape { virtual ~Shape() = default; virtual std::unique_ptr<Shape> clone() const = 0; virtual const char* name() const = 0; };
struct Circle : Shape {
    std::unique_ptr<Shape> clone() const override { return std::make_unique<Circle>(*this); }
    const char* name() const override { return "circle"; }
};'''),
      'What does this print?', 'circle', ['Shape', 'It does not compile'],
      'The virtual clone runs in Circle, which knows the concrete type to copy.')
drill('prototype-cloning','Predict output','A shallow copy shares state',
      M(r'''    Doc a{std::make_shared<std::string>("a")};
    Doc b = a;
    *b.text = "b";
    std::cout << *a.text << "\n";''', 'iostream memory string', r'''struct Doc { std::shared_ptr<std::string> text; };'''),
      'What does this print?', 'b', ['a', 'ab'],
      'Copying a shared_ptr copies the handle, not the string. A clone that must be independent has to copy the pointee.')
drill('prototype-cloning','Compiles?','Covariant smart pointers',
      M(r'''    return 0;''', 'memory', r'''struct B { virtual ~B() = default; virtual std::unique_ptr<B> clone() const = 0; };
struct D : B { std::unique_ptr<D> clone() const override { return std::make_unique<D>(*this); } };'''),
      'Does this program compile?', 'No: covariant return types apply only to raw pointers and references', ['Yes; unique_ptr<D> converts to unique_ptr<B>', 'Yes, because D derives from B'],
      'unique_ptr<D> is not derived from unique_ptr<B>, so it is a different return type, not a covariant one.', check='reject', diagnostic='different return type')

drill('queued-command-lifetime','Undefined behavior','A queued lambda capturing a local by reference',
      M(r'''    std::function<int()> cmd;
    {
        int value = 7;
        cmd = [&value] { return value; };
    }
    std::cout << cmd() << "\n";''', 'functional iostream'),
      'What is wrong with this program?', 'value has gone out of scope before the command runs', ['Nothing; the lambda keeps value alive', 'std::function copies value when it stores the lambda'],
      'A reference capture stores only an alias. Delayed execution needs a value capture or an ownership policy.', check='asan')
drill('queued-command-lifetime','Predict output','Capture by value snapshots',
      M(r'''    int v = 1;
    auto f = [v] { return v; };
    v = 2;
    std::cout << f() << "\n";''', 'iostream'),
      'What does this print?', '1', ['2', 'It does not compile'],
      'A value capture copies v when the lambda is created.')
drill('queued-command-lifetime','Predict output','A captured shared_ptr owns',
      M(r'''    auto p = std::make_shared<int>(1);
    std::function<void()> f = [p] {};
    std::cout << p.use_count() << "\n";''', 'functional iostream memory'),
      'What does this print?', '2', ['1', '3'],
      'The copied shared_ptr in the closure is a second owner, keeping the target alive as long as the command exists.')

drill('adapter-and-bridge','Undefined behavior','An adapter bound to a temporary',
      M(r'''    Adapter a{Legacy{"a configuration string well beyond small-string storage"}};
    std::cout << a.read() << "\n";''', 'iostream string', r'''struct Legacy { std::string text; std::string old_read() const { return text; } };
struct Adapter {
    const Legacy& target;
    explicit Adapter(const Legacy& l) : target(l) {}
    std::string read() const { return target.old_read(); }
};'''),
      'What is wrong with this program?', 'The temporary Legacy dies after the declaration, so the stored reference dangles', ['Nothing; reference members extend temporaries', 'It fails to compile'],
      'Binding a constructor parameter does not extend a temporary to the lifetime of a reference member.', check='asan')
drill('adapter-and-bridge','Predict output','Translating an error code',
      M(r'''    Adapter a;
    try { a.read(); } catch (const std::runtime_error& e) { std::cout << e.what(); }
    std::cout << "\n";''', 'iostream stdexcept', r'''struct Legacy { int old_read() const { return -1; } };
struct Adapter {
    Legacy legacy;
    int read() const { int r = legacy.old_read(); if (r < 0) throw std::runtime_error("read failed"); return r; }
};'''),
      'What does this print?', 'read failed', ['-1', 'Nothing is printed'],
      'An adapter translates the failure contract too, not just the function name.')
drill('adapter-and-bridge','Concept','Adapter versus bridge',
      '', 'What distinguishes a bridge from an adapter?', 'A bridge separates an abstraction from its implementation so both vary independently; an adapter converts an existing interface', ['A bridge always uses multiple inheritance', 'An adapter must own the adapted object'],
      'The patterns can look alike in code but solve different dependency problems.', check='reasoning')

drill('default-arguments','Predict output','Default arguments follow the static type',
      M(r'''    D d;
    B& b = d;
    b.f();
    d.f();
    std::cout << "\n";''', 'iostream', r'''struct B { virtual ~B() = default; virtual void f(int x = 1) { std::cout << "B" << x; } };
struct D : B { void f(int x = 2) override { std::cout << "D" << x; } };'''),
      'What does this print?', 'D1D2', ['D2D2', 'B1D2'],
      'The function body is chosen dynamically, but default arguments come from the declaration seen by the static type.')
drill('default-arguments','Predict output','Default arguments are evaluated per call',
      M(r'''    show();
    show();
    std::cout << "\n";''', 'iostream', r'''int n = 0;
int next() { return ++n; }
void show(int v = next()) { std::cout << v; }'''),
      'What does this print?', '12', ['11', '00'],
      'A default argument expression is evaluated each time the call uses it.')
drill('default-arguments','Compiles?','Repeating a default argument',
      M(r'''    g();''', 'iostream', r'''void g(int x = 1);
void g(int x = 1) { (void)x; }'''),
      'Does this program compile?', 'No: a default argument cannot be redefined in the same scope', ['Yes; identical defaults are allowed', 'Yes; the second one wins'],
      'Each parameter\'s default may be specified once per scope, even if the value is the same.', check='reject', diagnostic='redefinition of default argument')

drill('virtual-dispatch-cost','Layout','Size of a polymorphic empty class',
      M(r'''    std::cout << sizeof(E) << " " << sizeof(V) << "\n";''', 'iostream', r'''struct E {};
struct V { virtual ~V() = default; };'''),
      'On arm64 macOS, what does this print?', '1 8', ['0 8', '1 1'],
      'An empty class still has size one. A polymorphic class holds a hidden vtable pointer, eight bytes on LP64.')
drill('virtual-dispatch-cost','Predict output','A non-virtual function calling a virtual one',
      M(r'''    Derived d;
    d.run();
    std::cout << "\n";''', 'iostream', r'''struct Base { virtual ~Base() = default; void run() { std::cout << name(); } virtual const char* name() const { return "B"; } };
struct Derived : Base { const char* name() const override { return "D"; } };'''),
      'What does this print?', 'D', ['B', 'BD'],
      'run is not virtual, but its call to name() is a virtual call through this, so it reaches Derived::name.')
drill('virtual-dispatch-cost','Complexity','Where virtual calls cost',
      '', 'Why can a virtual call in a hot loop cost more than one indirect branch?', 'It usually prevents inlining unless the compiler can prove the dynamic type', ['Each virtual call allocates memory', 'Virtual calls copy the object'],
      'Without inlining, the optimizer cannot hoist or vectorize across the call. final and devirtualization can restore static knowledge.', check='reasoning')

drill('virtual-base-diamond','Predict output','Construction order with a virtual base',
      M(r'''    P p;
    std::cout << "\n";''', 'iostream', r'''struct D { D() { std::cout << "D"; } };
struct R : virtual D { R() { std::cout << "R"; } };
struct W : virtual D { W() { std::cout << "W"; } };
struct P : R, W { P() { std::cout << "P"; } };'''),
      'What does this print?', 'DRWP', ['DRDWP', 'RWDP'],
      'The most derived class constructs virtual bases first, once, then the non-virtual bases in declaration order.')
drill('virtual-base-diamond','Predict output','Who initializes the virtual base?',
      M(r'''    P p;
    std::cout << p.v << "\n";''', 'iostream', r'''struct D { int v; D(int x = 0) : v(x) {} };
struct R : virtual D { R() : D(1) {} };
struct W : virtual D { W() : D(2) {} };
struct P : R, W { P() {} };'''),
      'What does this print?', '0', ['1', '2'],
      'Only the most derived class initializes a virtual base. P does not name D, so D is default-constructed; R\'s and W\'s initializers are ignored.')
drill('virtual-base-diamond','Compiles?','Ambiguous member in a non-virtual diamond',
      M(r'''    P p;
    return p.id;''', 'iostream', r'''struct D { int id = 7; };
struct R : D {};
struct W : D {};
struct P : R, W {};'''),
      'Does this program compile?', 'No: id is found in two D subobjects', ['Yes, and it returns 7', 'Yes; the first base wins'],
      'Without virtual inheritance there are two D subobjects, and unqualified lookup is ambiguous.', check='reject', diagnostic='multiple base-class subobjects')

drill('padding-and-empty-members','Layout','Ordering members around a double',
      M(r'''    std::cout << sizeof(S) << " " << sizeof(R) << "\n";''', 'iostream', r'''struct S { char c; double d; char e; };
struct R { double d; char c; char e; };'''),
      'On arm64 macOS, what does this print?', '24 16', ['10 10', '16 16'],
      'In S, c is padded to 8 before d and e is padded at the end to 24. R needs only 6 bytes of tail padding.')
drill('padding-and-empty-members','Layout','Empty base versus empty member',
      M(r'''    std::cout << sizeof(Base) << " " << sizeof(Member) << "\n";''', 'iostream', r'''struct E {};
struct Base : E { int x; };
struct Member { E e; int x; };'''),
      'On arm64 macOS, what does this print?', '4 8', ['8 8', '4 4'],
      'The empty base optimization lets E occupy no storage. An ordinary empty member needs one byte, padded to int alignment.', standard=14)
drill('padding-and-empty-members','Layout','Two empty members of the same type',
      M(r'''    T t;
    std::cout << sizeof(T) << " " << ((void*)&t.a != (void*)&t.b) << "\n";''', 'iostream', r'''struct E {};
struct T { [[no_unique_address]] E a; [[no_unique_address]] E b; int x; };'''),
      'Compiled as C++20 on arm64 macOS, what does this print?', '4 1', ['4 0', '8 1'],
      'Both members can overlap x, but two objects of the same type must still have distinct addresses.')

drill('override-and-final','Compiles?','override with a different parameter type',
      M(r'''    return 0;''', 'iostream', r'''struct B { virtual ~B() = default; virtual void f(int) {} };
struct D : B { void f(long) override {} };'''),
      'Does this program compile?', 'No: f(long) does not override f(int), so override is an error', ['Yes; long converts from int', 'Yes, with a warning'],
      'Overriding requires matching parameter types. override turns the mismatch into a diagnostic.', check='reject', diagnostic="marked 'override'")
drill('override-and-final','Compiles?','Deriving from a final class',
      M(r'''    return 0;''', 'iostream', r'''struct X final {};
struct Y : X {};'''),
      'Does this program compile?', 'No: a final class cannot be a base', ['Yes; final only affects virtual functions', 'Yes, but Y cannot be instantiated'],
      'final on a class forbids derivation entirely.', check='reject', diagnostic="is marked 'final'")
drill('override-and-final','Predict output','A missing const creates a new function',
      M(r'''    D d;
    B& b = d;
    std::cout << b.f() << d.f() << "\n";''', 'iostream', r'''struct B { virtual ~B() = default; virtual const char* f() const { return "B"; } };
struct D : B { const char* f() { return "D"; } };'''),
      'What does this print?', 'BD', ['DD', 'BB'],
      'D::f is not const, so it does not override B::f. The call through B& runs B::f; the call on non-const d picks D::f.')

drill('pimpl-firewall','Compiles?','Implicit destructor with an incomplete Impl',
      M(r'''    W w;
    (void)w;''', 'memory', r'''struct W { struct Impl; std::unique_ptr<Impl> p; };'''),
      'Does this program compile?', 'No: the implicit destructor instantiates unique_ptr\'s deleter on an incomplete type', ['Yes; unique_ptr never needs the complete type', 'Yes, and the pointer is simply null'],
      'Declare ~W() in the class and define it where Impl is complete.', check='reject', diagnostic='incomplete type')
drill('pimpl-firewall','Compiles?','Copying a move-only pimpl class',
      M(r'''    Widget a;
    Widget b = a;
    (void)b;''', 'memory', r'''class Widget {
public:
    Widget() : p(new int(1)) {}
    Widget(Widget&&) noexcept = default;
    ~Widget() = default;
private:
    std::unique_ptr<int> p;
};'''),
      'Does this program compile?', 'No: declaring the move constructor deletes the implicit copy constructor', ['Yes; the pointer is copied shallowly', 'Yes; the unique_ptr is cloned'],
      'A pimpl class needs an explicit deep-copy constructor if copying is part of its contract.', check='reject', diagnostic='implicitly-deleted copy constructor')
drill('pimpl-firewall','Concept','What pimpl costs',
      '', 'What does the pimpl idiom trade for its compilation firewall?', 'A heap allocation per object and an extra indirection on each access', ['Virtual dispatch on every member function', 'The ability to have private members'],
      'Clients see only a pointer, so representation changes do not recompile them, but every object owns a separate allocation.', check='reasoning')

drill('implicit-move-suppression','Copies and moves','A user-declared copy constructor',
      M(r'''    X a;
    X b = std::move(a);
    (void)b;''', 'iostream utility', r'''struct Probe { Probe() = default; Probe(const Probe&) { std::cout << "copy\n"; } Probe(Probe&&) noexcept { std::cout << "move\n"; } };
struct X { Probe p; X() = default; X(const X& o) : p(o.p) {} };'''),
      'What does this print?', 'copy', ['move', 'It does not compile'],
      'A user-declared copy constructor suppresses the implicit move constructor, so the rvalue binds to const X&.')
drill('implicit-move-suppression','Copies and moves','A defaulted destructor still counts',
      M(r'''    Y a;
    Y b = std::move(a);
    (void)b;''', 'iostream utility', r'''struct Probe { Probe() = default; Probe(const Probe&) { std::cout << "copy\n"; } Probe(Probe&&) noexcept { std::cout << "move\n"; } };
struct Y { Probe p; ~Y() = default; };'''),
      'What does this print?', 'copy', ['move', 'Nothing is printed'],
      '= default still makes the destructor user-declared, which suppresses the implicit move operations.')
drill('implicit-move-suppression','Copies and moves','Rule of zero restores the move',
      M(r'''    W a;
    W b = std::move(a);
    (void)b;''', 'iostream string utility', r'''struct Probe { Probe() = default; Probe(const Probe&) { std::cout << "copy\n"; } Probe(Probe&&) noexcept { std::cout << "move\n"; } };
struct W { Probe p; std::string s; };'''),
      'What does this print?', 'move', ['copy', 'copy then move'],
      'With no user-declared special members, W\'s implicit move constructor moves each member.')

drill('explicit-conversions','Compiles?','Copy-initialization with an explicit constructor',
      M(r'''    Meters m = 2.0;
    (void)m;''', 'iostream', r'''struct Meters { explicit Meters(double v) : v(v) {} double v; };'''),
      'Does this program compile?', 'No: copy-initialization does not consider explicit constructors', ['Yes; 2.0 converts implicitly', 'Yes, but m is zero'],
      'Write Meters m{2.0} or Meters m(2.0) to call an explicit constructor.', check='reject', diagnostic='no viable conversion')
drill('explicit-conversions','Predict output','Contextual conversions of explicit operator bool',
      M(r'''    H a{1}, b{0};
    std::cout << (a && !b) << (b || a) << "\n";''', 'iostream', r'''struct H { int fd; explicit operator bool() const { return fd != 0; } };'''),
      'What does this print?', '11', ['10', 'It does not compile'],
      'The operands of the built-in logical operators are contextually converted to bool, so explicit operator bool is allowed.')
drill('explicit-conversions','Predict output','An implicit converting constructor',
      M(r'''    print('A');
    std::cout << "\n";''', 'iostream', r'''struct Str { Str(int n) : len(n) {} int len; };
void print(Str s) { std::cout << s.len; }'''),
      'What does this print?', '65', ['A', 'It does not compile'],
      'char promotes to int and the non-explicit constructor converts it to Str. Marking it explicit would reject this call.')

drill('inline-static-members','Predict output','One static member for all objects',
      M(r'''    Counter a, b;
    a.count = 5;
    std::cout << b.count << "\n";''', 'iostream', r'''struct Counter { inline static int count = 0; };'''),
      'What does this print?', '5', ['0', 'It does not compile'],
      'a.count and b.count name the same class-level variable.')
drill('inline-static-members','Compiles?','A non-const static initializer in C++14',
      M(r'''    return C::x;''', 'iostream', r'''struct C { static int x = 1; };'''),
      'Compiled as C++14, does this program compile?', 'No: a non-const static data member must be initialized out of line', ['Yes; the initializer is a definition', 'Yes, but it links only once'],
      'Before C++17 inline variables, only const integral or constexpr static members could have in-class initializers.', check='reject', diagnostic='must be initialized out of line', standard=14)
drill('inline-static-members','Layout','Static members do not occupy object storage',
      M(r'''    std::cout << sizeof(C) << "\n";''', 'iostream', r'''struct C { inline static int n = 0; inline static double d = 1.0; char c; };'''),
      'What does this print?', '1', ['13', '16'],
      'Static data members live outside every object; only c contributes to the size.')

drill('user-defined-literals','Predict output','Which literal operator is chosen?',
      M(r'''    std::cout << 2_u << " " << 2.0_u << "\n";''', 'iostream', r'''const char* operator""_u(unsigned long long) { return "integer"; }
const char* operator""_u(long double) { return "floating"; }'''),
      'What does this print?', 'integer floating', ['integer integer', 'floating floating'],
      'Integer literals use the unsigned long long form and floating literals use the long double form.')
drill('user-defined-literals','Compiles?','A negative literal with a suffix',
      M(r'''    auto d = -5_m;
    (void)d;''', 'iostream', r'''struct Dist { long double m; };
constexpr Dist operator""_m(unsigned long long v) { return Dist{static_cast<long double>(v)}; }'''),
      'Does this program compile?', 'No: the minus is a unary operator applied to Dist, which has no operator-', ['Yes; the literal operator receives -5', 'Yes; unsigned long long wraps the value'],
      'Numeric literals have no sign. -5_m means -(5_m).', check='reject', diagnostic='invalid argument type')
drill('user-defined-literals','Predict output','The standard s suffix keeps embedded nulls',
      M(r'''    using namespace std::string_literals;
    auto a = "ab\0c"s;
    std::string b = "ab\0c";
    std::cout << a.size() << " " << b.size() << "\n";''', 'iostream string'),
      'What does this print?', '4 2', ['4 4', '2 2'],
      'The s literal operator receives the full length. Constructing from a const char* stops at the first null character.')

drill('construction-dispatch','Predict output','Each constructor sees its own class',
      M(r'''    C c;
    std::cout << "\n";''', 'iostream', r'''struct A { A() { std::cout << n(); } virtual ~A() = default; virtual const char* n() const { return "A"; } };
struct B : A { B() { std::cout << n(); } const char* n() const override { return "B"; } };
struct C : B { C() { std::cout << n(); } const char* n() const override { return "C"; } };'''),
      'What does this print?', 'ABC', ['CCC', 'AAA'],
      'During each constructor, the dynamic type is the class being constructed, so dispatch stops there.')
drill('construction-dispatch','Concept','A pure virtual call during construction',
      '', 'A base constructor calls a non-virtual helper that calls a pure virtual function. What is the outcome?', 'Undefined behavior; implementations commonly abort with a pure virtual call error', ['The derived override runs', 'The call is skipped'],
      'During base construction no override is selected, and calling a pure virtual through dispatch has undefined behavior.', check='reasoning')
drill('construction-dispatch','Predict output','dynamic_cast inside a base constructor',
      M(r'''    D d;
    (void)d;
    std::cout << "\n";''', 'iostream', r'''struct D;
struct B { B(); virtual ~B() = default; };
struct D : B {};
B::B() { std::cout << (dynamic_cast<D*>(this) == nullptr); }'''),
      'What does this print?', '1', ['0', 'It does not compile'],
      'While B is being constructed, the object\'s dynamic type is B, so a cast to D fails.')

drill('non-virtual-interface','Predict output','The base enforces a postcondition',
      M(r'''    Long l;
    const Source& s = l;
    std::cout << s.read() << "\n";''', 'iostream string', r'''class Source {
public:
    virtual ~Source() = default;
    std::string read() const { std::string r = do_read(); return r.size() > 3 ? r.substr(0, 3) : r; }
private:
    virtual std::string do_read() const = 0;
};
class Long : public Source { std::string do_read() const override { return "abcdef"; } };'''),
      'What does this print?', 'abc', ['abcdef', 'It does not compile'],
      'The public non-virtual wrapper applies the size limit to every implementation.')
drill('non-virtual-interface','Compiles?','Calling the private hook directly',
      M(r'''    Upper u;
    return u.step();''', 'iostream', r'''struct Base { virtual ~Base() = default; int run() { return step(); } private: virtual int step() { return 1; } };
struct Upper : Base { private: int step() override { return 2; } };'''),
      'Does this program compile?', 'No: step is private in Upper', ['Yes, and main returns 2', 'Yes, and main returns 1'],
      'Access is checked on the name in the class used for lookup; clients must go through run().', check='reject', diagnostic='private member')
drill('non-virtual-interface','Predict output','An override with a different access level',
      M(r'''    D d;
    d.run();
    d.step();
    std::cout << "\n";''', 'iostream', r'''struct B { virtual ~B() = default; void run() { step(); } private: virtual void step() { std::cout << "B"; } };
struct D : B { public: void step() override { std::cout << "D"; } };'''),
      'What does this print?', 'DD', ['BD', 'It does not compile'],
      'D may override the private B::step and declare it public. run dispatches to D::step, and D\'s public access permits the direct call.')

drill('access-per-class','Compiles?','Friendship is not inherited',
      M(r'''    return 0;''', 'iostream', r'''class Account { int balance_ = 0; friend class Auditor; };
class Auditor {};
class SubAuditor : public Auditor { public: int peek(const Account& a) { return a.balance_; } };'''),
      'Does this program compile?', 'No: SubAuditor is not a friend of Account', ['Yes; it inherits Auditor\'s friendship', 'Yes, because peek is public'],
      'Friendship is granted to a specific class and is neither inherited nor transitive.', check='reject', diagnostic='private member')
drill('access-per-class','Predict output','Swapping private state of another object',
      M(r'''    Box a(1), b(2);
    a.swap_with(b);
    std::cout << a.get() << b.get() << "\n";''', 'iostream', r'''class Box {
    int v_;
public:
    explicit Box(int v) : v_(v) {}
    void swap_with(Box& o) { int t = v_; v_ = o.v_; o.v_ = t; }
    int get() const { return v_; }
};'''),
      'What does this print?', '21', ['12', 'It does not compile'],
      'Member functions of Box may access private members of any Box object.')
drill('access-per-class','Compiles?','Protected access through a base reference',
      M(r'''    return 0;''', 'iostream', r'''struct B { protected: int x = 1; };
struct D : B { int peek(B& b) { return b.x; } };'''),
      'Does this program compile?', 'No: D may access protected x only through D objects', ['Yes; D derives from B', 'Yes, because x is not private'],
      'Protected access from a derived class requires the object expression to be of the derived type, preventing access to unrelated siblings.', check='reject', diagnostic='protected member')
