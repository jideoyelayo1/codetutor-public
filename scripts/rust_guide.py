"""Original, versioned Rust guide; content is preformatted and generation is offline."""
import json
from pathlib import Path

LESSONS = json.loads(Path(__file__).with_name("rust_guide_content.json").read_text())
BOOK = "https://doc.rust-lang.org/1.99.0/book/"
COURSE = dict(id='guide.rust', title='Rust: from first program to advanced systems', kind='Language guide',
    edition='Rust 1.99.0 · Edition 2024 · checked 16 October 2026',
    scope='An ordered guide with explanations, runnable examples, practice, answers, checkpoints, recall, a procedural-macro workspace, a tested CLI, Cargo features/build scripts and a bounded HTTP server, then quant and systems stages 15-19 (language depth, numerics, performance engineering, market-systems projects and interview drills) with extra checkpoint questions. Complete language/reference and source-exercise depth coverage remains under audit.',
    trackIDs=['rust'],
    sourceURL=BOOK)


def apply(content):
    """Append a new guide without editing or renumbering any previous record."""
    # Imported here so the backend can load this module as scripts.rust_guide for LESSONS alone.
    from guide_builder import apply_guide
    return apply_guide(content, LESSONS, 'rust', 'Rust 1.99 reference and learning sources', 'Rust 1.99 source reference',
        'Original guided lessons and checked examples; reference-level depth audit ongoing', COURSE)
