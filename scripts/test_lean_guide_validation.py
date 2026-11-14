"""Keep focused development checks from overwriting the full Lean acceptance receipt."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from owned_process import run_owned

ROOT = Path(__file__).resolve().parent.parent


class LeanGuideValidationTests(unittest.TestCase):
    def test_focused_validation_cannot_replace_full_receipt(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.build') as directory:
            # A broken guard must not damage the real acceptance receipt.
            fixture = Path(directory)/'repo'
            (fixture/'scripts').mkdir(parents=True); (fixture/'docs').mkdir()
            for name in ['validate_lean_guide.py', 'owned_process.py']:
                (fixture/'scripts'/name).write_bytes((ROOT/'scripts'/name).read_bytes())
            full = fixture/'docs/lean-guide-validation.json'; full.write_text('{"full":true}\n')
            before = hashlib.sha256(full.read_bytes()).hexdigest()
            link = Path(directory)/'report.json'; link.symlink_to(full)
            for target in [None, Path('docs/lean-guide-validation.json'), full, link]:
                with self.subTest(target=target):
                    command = [sys.executable, str(fixture/'scripts/validate_lean_guide.py'), '--lesson', 's01-eval-and-check']
                    if target: command += ['--report', str(target)]
                    result = run_owned(command, cwd=fixture, timeout=10)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(hashlib.sha256(full.read_bytes()).hexdigest(), before)


if __name__ == '__main__':
    unittest.main()
