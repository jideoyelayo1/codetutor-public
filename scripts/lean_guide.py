"""Original, versioned Lean 4 guide; content is preformatted and generation is offline."""
import json
from pathlib import Path

LESSONS = json.loads(Path(__file__).with_name("lean_guide_content.json").read_text())
COURSE = dict(id='guide.lean', title='Lean 4: from first program to proofs and metaprogramming', kind='Language guide',
    edition='Lean 4.35.0 · Mathlib v4.35.0 · checked 15 October 2026',
    scope='An ordered guide with explanations, compiler-checked examples, practice, answers, checkpoints and recall across three connected paths: functional programming, mathematics and proof, and metaprogramming. Mathlib lessons were checked in a pinned authoring project; the hosted runner checks single files without Mathlib. Exhaustive book-subsection and exercise adaptation remains under audit.',
    trackIDs=['lean'],
    sourceURL='https://lean-lang.org/learn/')


def apply(content):
    """Append the Lean guide without editing or renumbering any previous record."""
    if not LESSONS: return content
    # Imported here so the backend can load this module as scripts.lean_guide for LESSONS alone.
    from guide_builder import apply_guide
    return apply_guide(content, LESSONS, 'lean', 'Lean 4.35 reference and learning sources', 'Lean 4.35 source reference',
        'Original guided lessons and checked examples; reference-level depth audit ongoing', COURSE)
