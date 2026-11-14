"""Original data-model teaching companions for bounded first-edition source sections."""
from python_guide_depth import add, task, DEPTH

add('special-method-lookup', 'Data model 3.3.13: implicit special method lookup',
    'https://docs.python.org/3.13/reference/datamodel.html#special-method-lookup', [
    "Special methods connect an object's type to language operations. Implement __len__ on the class so len(instance) has a defined meaning. Normally call the public operation, not a special method directly, because Python can apply additional protocol rules around that operation.",
    "Implicit special-method lookup differs from ordinary instance attribute lookup. Assigning a new instance.__len__ attribute can change an explicit instance.__len__() call while len(instance) still uses the type's implementation. The worked example intentionally contrasts those two lookups; it is a diagnostic demonstration, not a recommended monkey-patching API.",
    "The length protocol also checks its result. A negative length is invalid, and a string is not an integer length. Do not infer these checks from a method merely existing. The transfer exercise observes valid lengths and the actual exception categories for invalid return values.",
    "The supplied book introduces the benefit of familiar built-in operations. The current Python reference supplies the more precise type-lookup rule used here. This lesson does not benchmark CPython's internal length fields or certify every interpreter's implementation strategy."
    ],
    ("Why can len(obj) differ from obj.__len__() after assigning an instance attribute named __len__?",
     "Implicit len lookup uses the type's special method, while ordinary explicit lookup can find the instance attribute.",
     ["len always reads whichever instance attribute was assigned most recently.", "Every object stores length in a public field named length.", "An explicit method call and every language operation must use identical lookup rules."],
     "Implicit special operations have special lookup rules on the type. This lets the example distinguish the protocol from a plain attribute call."),
    task("Transfer: observe invalid length results",
         "A Count object returns data directly from its class-defined __len__. data is 0, 3, -1 or '3'. Return len(obj) when accepted, otherwise the ValueError/TypeError class name. Do not coerce the supplied return value.",
         "class Count:\n    def __len__(self):\n        return data\ntry:\n    result = len(Count())\nexcept (ValueError, TypeError) as error:\n    result = type(error).__name__",
         [(0,0),(3,3),(-1,'ValueError'),('3','TypeError')],
         ("return data","return abs(data)"),
         ["Let len enforce its protocol instead of pre-coercing the result.", "A negative length violates the nonnegative rule.", "Text '3' is a different return type from integer three."],
         "Zero and three are valid lengths. A negative return raises ValueError, and a string raises TypeError. Applying abs would hide the negative-result violation rather than faithfully observing it.",
         ['ValueError','TypeError',None]),
    ("Where should a custom length implementation live?", "On the class as __len__. The public len operation uses the type's special lookup and validates the returned length."))

add('sequence-protocol', 'Data model: object.__getitem__, iteration fallback and sequence operations',
    'https://docs.python.org/3.13/reference/datamodel.html#object.__getitem__', [
    "A small read-only sequence can compose an owned tuple and delegate indexed lookup to it. Integers, negative indices and slice objects then retain the tuple's bounds behavior. The class needs to state what a slice returns; here it returns the backing tuple's selected values rather than inventing a new domain object.",
    "When __iter__ is absent, Python can iterate through integer __getitem__ requests beginning at zero until IndexError. Membership can use that iteration fallback, while reversed can use length and indexed access. Supporting familiar operations is a set of behavioral promises, not simply having methods with particular names.",
    "A read-only element API does not establish deep immutability of arbitrary nested objects or a security boundary around attributes. This lesson stores integer values in a tuple and intentionally omits __setitem__. Assignment through obj[index] therefore raises TypeError. A mutable sequence or shuffle operation would need additional behavior.",
    "The original source demonstrates interoperability with a card collection. This original measurement-window exercise checks negative indexing, iteration, membership, slicing, sorting and reverse traversal with small integer data. It does not claim implementation of every collections.abc.Sequence method."
    ],
    ("Why must a fallback sequence iterator eventually receive IndexError from __getitem__?",
     "That exception marks exhaustion when iteration requests successive integer positions.",
     ["Returning the first item forever makes iteration complete automatically.", "A custom __iter__ is mandatory for every iterable.", "Membership can never use iteration."],
     "The fallback needs a finite stopping signal. Delegating to the tuple preserves its out-of-bounds IndexError behavior."),
    task("Transfer: interoperability without mutation",
         "data is an integer list. Define Readings with an owned tuple, __len__ and delegated __getitem__, without __iter__ or __setitem__. Return [last_or_None, sorted_values, reversed_values, item_assignment_accepted].",
         "class Readings:\n    def __init__(self, items):\n        self._items = tuple(items)\n    def __len__(self):\n        return len(self._items)\n    def __getitem__(self, key):\n        return self._items[key]\nwindow = Readings(data)\nlast = window[-1] if len(window) else None\ntry:\n    window[0] = 99\n    editable = True\nexcept TypeError:\n    editable = False\nresult = [last, sorted(window), list(reversed(window)), editable]",
         [([3,1,2],[2,[1,2,3],[2,1,3],False]),([],[None,[],[],False]),([0],[0,[0],[0],False]),([-2,4],[4,[-2,4],[4,-2],False])],
         ("return self._items[key]","return self._items[key] * 2"),
         ["Delegate the key unchanged to the tuple.", "Preserve IndexError at exhaustion for fallback iteration.", "Use the public operations and separately observe rejected item assignment."],
         "The original order is 3,1,2, so reverse traversal yields 2,1,3 while sorted returns 1,2,3. Last is two. Item assignment is rejected because no writable-element protocol is defined.",
         [[2,[3,1,2],[2,1,3],False],[2,[1,2,3],[3,1,2],False],[2,[1,2,3],[2,1,3],True]]),
    ("What does a read-only sequence surface not guarantee?", "It omits element assignment through that API; it does not automatically provide deep immutability, attribute security or every abstract-sequence method."))

add('object-representation', 'Data model: object.__repr__ and object.__str__',
    'https://docs.python.org/3.13/reference/datamodel.html#object.__repr__', [
    "Diagnostic and user-facing text have different jobs. repr should make the object's relevant state unambiguous, including whether a field contains quotes or newlines. str can choose a readable display value. If __str__ is absent, the default display behavior can fall back to __repr__.",
    "The !r conversion inside an f-string asks for the field's representation. It preserves quoting and escape distinctions that inserting a raw string would lose. A useful representation can resemble construction syntax, but do not assume that evaluating arbitrary representation text is a safe or complete serialization format.",
    "Containers such as lists use their elements' representations in their own repr output. This makes a good __repr__ useful when inspecting a collection of domain objects, even if direct printing of one object uses its simpler __str__.",
    "The fixture includes an embedded newline and empty text. These values can appear deceptively similar in casual output, but their diagnostic representations need to remain distinct. The task supplies complete object definitions and compares actual strings, not screenshots of a console."
    ],
    ("Why is !r appropriate for a text field inside a diagnostic representation?",
     "It retains quoting and escape information that raw display text can hide.",
     ["It turns every representation into a safe general-purpose persistence format.", "It changes the underlying text value.", "Lists always use __str__ for their elements' repr output."],
     "A diagnostic needs to distinguish field contents. Representation is still not an instruction to evaluate untrusted text."),
    task("Transfer: inspect an object and a collection",
         "data is a string. Note.__repr__ must produce Note(text=<repr of text>), while __str__ returns the text itself. Return [repr(note), str(note), repr([note])].",
         "class Note:\n    def __init__(self, text):\n        self.text = text\n    def __repr__(self):\n        return f'Note(text={self.text!r})'\n    def __str__(self):\n        return self.text\nnote = Note(data)\nresult = [repr(note), str(note), repr([note])]",
         [('x',["Note(text='x')",'x',"[Note(text='x')]"]),('line\nnext',["Note(text='line\\nnext')",'line\nnext',"[Note(text='line\\nnext')]"]),('',["Note(text='')",'',"[Note(text='')]"])],
         ("f'Note(text={self.text!r})'","f'Note(text={self.text})'"),
         ["Use !r on the field inside __repr__.", "Keep __str__ separate from the diagnostic constructor-like text.", "The enclosing list's repr will call the element's representation."],
         "The standalone representation and the list's element representation retain the same quoted text. The display string remains x. Removing !r loses the quoted-field distinction and mishandles embedded newlines.",
         [["Note(text=x)",'x',"[Note(text=x)]"],['x','x',"['x']"],["Note(text='x')","Note(text='x')","[Note(text='x')]"]]),
    ("Is a constructor-like repr a general safe serialization format?", "No. It is diagnostic text. Persistence and reconstructing trusted data need their own explicit format and validation policy."))

add('truth-protocol', 'Data model: object.__bool__ / required Boolean return and length fallback',
    'https://docs.python.org/3.13/reference/datamodel.html#object.__bool__', [
    "bool(obj) first uses __bool__ when the type supplies it. Otherwise a defined __len__ can provide truth through zero versus nonzero length. With neither method, ordinary user-defined instances are truthy by default.",
    "A custom __bool__ must return a Boolean. Returning a truthy list or integer is not accepted merely because an if statement could test that value by itself. Implement a predicate or explicitly convert the intended domain expression when writing a valid class.",
    "Choose the predicate from the domain rather than an incidental sign or storage detail. A numeric delta with negative magnitude is still nonzero, so amount > 0 would implement positivity instead of numeric truth. In another domain, truth might mean a validated signal exists; that policy should be documented.",
    "The transfer task intentionally supplies valid and invalid raw method returns and observes the actual protocol boundary. It does not silently repair the invalid return by coercion, because that would hide the behavior being taught."
    ],
    ("Can __bool__ return a truthy integer or list instead of a Boolean?",
     "No. Its return must satisfy the Boolean-return protocol or bool(obj) raises TypeError.",
     ["Yes, any truthy value is automatically accepted.", "It must return the object's length.", "Only False is allowed as a custom return."],
     "Truth-testing an arbitrary object and implementing __bool__ are different operations. The special method has a stricter return contract."),
    task("Transfer: observe the Boolean-return boundary",
         "Flag.__bool__ returns data directly. Return bool(Flag()) for valid Boolean returns, or 'TypeError' for an invalid return. data is True, False, 1 or an empty list. Do not coerce the method's result inside the class.",
         "class Flag:\n    def __bool__(self):\n        return data\ntry:\n    result = bool(Flag())\nexcept TypeError:\n    result = 'TypeError'",
         [(True,True),(False,False),(1,'TypeError'),([],'TypeError')],
         ("return data","return bool(data)"),
         ["Distinguish the special method's return contract from general truthiness.", "Let bool(Flag()) expose a bad return.", "Integer one is truthy in ordinary conditions but is not a Boolean return object here."],
         "True and False pass through the protocol. Returning integer one or an empty list raises TypeError. Coercing inside the method changes the observation and hides those invalid raw returns.",
         [False,'TypeError',1]),
    ("What is the custom-object truth fallback order?", "Use __bool__ when defined, otherwise __len__ when defined, otherwise ordinary instances are truthy. __bool__ itself must return a Boolean."))

add('numeric-dispatch', 'Data model: binary arithmetic and reflected fallback',
    'https://docs.python.org/3.13/reference/datamodel.html#emulating-numeric-types', [
    "A binary special method must decide which operand types it supports. Return NotImplemented for an unsupported combination when Python should try the remaining dispatch rules. The singleton is not the exception class NotImplementedError and is not a fabricated successful answer.",
    "A compatible right operand can supply a reflected operation such as __radd__. Raising TypeError immediately from the left method can prevent that fallback. Once both sides decline the operation, Python reports the unsupported pair as TypeError.",
    "Nonmutating arithmetic normally returns a new result object and leaves both operands' observed values intact. This is a stated policy here, not a claim that every Python operator on every type is immutable. Augmented assignment has additional semantics and separate tests.",
    "The original book's early arithmetic example leaves reflected multiplication for a later chapter. This original transfer exercise adds both multiplication directions explicitly and checks equality of their values while retaining the operand. Subclass dispatch priority and the full numeric tower remain beyond this bounded lab."
    ],
    ("Why return NotImplemented instead of immediately raising for an unsupported operand type?",
     "It permits Python to try the other applicable dispatch paths, including a compatible reflected method.",
     ["It is identical to raising NotImplementedError.", "It guarantees that the unsupported operation succeeds.", "It means returning a default numeric zero."],
     "Returning the singleton participates in dispatch. If all relevant implementations decline, Python can then raise TypeError."),
    task("Transfer: scalar multiplication in either order",
         "data is [amount, integer_scale]. Define Shift.__mul__ to create a new Shift for an int scale and return NotImplemented otherwise. Define __rmul__ consistently. Return [right_scaled_amount, left_scaled_amount, original_amount].",
         "class Shift:\n    def __init__(self, amount):\n        self.amount = amount\n    def __mul__(self, scalar):\n        if type(scalar) is not int:\n            return NotImplemented\n        return Shift(self.amount * scalar)\n    def __rmul__(self, scalar):\n        return self * scalar\namount, scale = data\noriginal = Shift(amount)\nresult = [(original * scale).amount, (scale * original).amount, original.amount]",
         [([3,2],[6,6,3]),([-2,3],[-6,-6,-2]),([0,7],[0,0,0]),([5,0],[0,0,5])],
         ("return self * scalar","return Shift(self.amount + scalar)"),
         ["Use one multiplication policy for both operand orders.", "Return a new Shift rather than updating the operand.", "A zero scale produces zero in either direction while preserving the original."],
         "Three scaled by two gives six regardless of operand order, and the original still stores three. A reflected method that adds instead of multiplying violates only one direction, so both directions must be tested.",
         [[6,5,3],[6,6,6],[5,5,3]]),
    ("What should a numeric interoperability test observe?", "Supported operand orders, unsupported-type fallback and whether operand mutation matches the stated arithmetic policy."))

add('magnitude-protocol', 'Data model: object.__abs__ / a numeric magnitude contract',
    'https://docs.python.org/3.13/reference/datamodel.html#object.__abs__', [
    "abs is another public operation that a domain object can implement through a special method. For orthogonal components x and y, the Euclidean magnitude is hypot(x,y), not their signed sum. Changing a component's sign does not change that magnitude.",
    "Using math.hypot states the intended magnitude directly and avoids manually expanding this calculation into an unexamined square/sum/square-root sequence. That API choice does not establish acceptable error for every application or every scale; numerical stability receives its own later stage.",
    "Clipping a two-component measurement to a maximum magnitude scales both components by the same factor. Preserve its direction when nonzero. A zero measurement needs an explicit branch to avoid division by zero; a zero cap turns any nonzero measurement into zero.",
    "The transfer fixture reports the original magnitude, scaled components and factor. It checks a measurement already inside the cap, one that needs clipping, the zero measurement and a zero cap. These cases reveal reversed-ratio and missing-zero-guard errors."
    ],
    ("Why is a signed sum unsuitable as a two-component Euclidean magnitude?",
     "Opposite signs can cancel even when the components describe a nonzero magnitude.",
     ["Magnitude is allowed to depend only on the first component.", "A norm must always be an integer.", "Negative components are invalid for every vector-like object."],
     "Magnitude describes size independently of those sign directions. hypot applies the Euclidean formula."),
    task("Transfer: clip a measurement magnitude",
         "data is [[x,y], nonnegative_cap], with small finite numeric values. Define Components.__abs__ using hypot. Return [original_magnitude, clipped_components, factor], preserving direction and leaving zero unchanged with factor 1.",
         "class Components:\n    def __init__(self, x, y):\n        self.x, self.y = x, y\n    def __abs__(self):\n        return math.hypot(self.x, self.y)\ncoordinates, cap = data\nvalue = Components(*coordinates)\nmagnitude = abs(value)\nfactor = 1.0 if magnitude == 0 or magnitude <= cap else cap / magnitude\nresult = [magnitude, [value.x * factor, value.y * factor], factor]",
         [([[3,4],10],[5.0,[3.0,4.0],1.0]),([[3,4],2.5],[5.0,[1.5,2.0],0.5]),([[0,0],0],[0.0,[0.0,0.0],1.0]),([[-3,4],0],[5.0,[-0.0,0.0],0.0])],
         ("cap / magnitude","magnitude / cap"),
         ["Obtain magnitude through the public abs operation.", "Handle zero before division.", "When clipping, cap divided by magnitude is at most one."],
         "The 3/4 components have magnitude five. A cap of 2.5 gives factor one half and components 1.5/2. A zero measurement keeps factor one; a zero cap scales a nonzero measurement to zero.",
         [[7.0,[3.0,4.0],1.0],[5.0,[6.0,8.0],2.0],[5.0,[1.5,2.0],0.5]], "import math"),
    ("What boundary cases should magnitude clipping include?", "Already inside the cap, above it, zero magnitude and zero cap; check the factor, direction and scaled values together."))

