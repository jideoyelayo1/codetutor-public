"""Original, versioned Bash guide; content is preformatted and generation is offline."""
import json
from pathlib import Path

LESSONS = json.loads(Path(__file__).with_name("bash_guide_content.json").read_text())
MANUAL = "https://www.gnu.org/software/bash/manual/bash.html"


def apply(content):
    """Append the Bash guide after every existing record so earlier IDs and orders stay stable."""
    # Imported here, as in rust_guide.py, so the module also loads as scripts.bash_guide.
    from guide_builder import apply_guide
    return apply_guide(content, LESSONS, 'bash', 'Bash 5.3 manual and shell references', 'Bash 5.3 reference',
        'Original guided lessons and checked scripts; manual-level depth audit ongoing',
        dict(id='guide.bash',title='Bash: from first command to expert scripting',kind='Language guide',edition='GNU Bash 5.3 (patch 20) · ShellCheck 0.11.0 · checked 16 October 2026',scope='An ordered guide with explanations, runnable scripts, practice, answers, checkpoints, recall and tested multi-file projects, from the first command to robust, debuggable and portable automation. Every bundled script runs under Bash 5.3 in a clean environment and passes ShellCheck unless a pitfall is deliberately shown. Not every manual subsection or interactive/readline feature is exhaustively adapted.',trackIDs=['bash'],sourceURL=MANUAL,chapters=None))
