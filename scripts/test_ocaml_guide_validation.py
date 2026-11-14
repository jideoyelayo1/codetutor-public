"""Keep focused development checks from overwriting the full acceptance receipt."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from owned_process import run_owned

ROOT=Path(__file__).resolve().parent.parent


class OcamlGuideValidationTests(unittest.TestCase):
    def test_focused_validation_cannot_replace_full_receipt(self):
        (ROOT/'.build').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.build') as directory:
            # A broken guard must not damage the real acceptance receipt.
            fixture=Path(directory)/'repo'
            (fixture/'scripts/ocaml_guide_content').mkdir(parents=True);(fixture/'docs').mkdir()
            for name in ['validate_ocaml_guide.py','ocaml_guide.py','owned_process.py']:
                (fixture/'scripts'/name).write_bytes((ROOT/'scripts'/name).read_bytes())
            (fixture/'scripts/ocaml_guide_content/01.json').write_text('[{"key":"first-program","stage":"01"}]')
            full=fixture/'docs/ocaml-guide-validation.json';full.write_text('{"full":true}\n')
            before=hashlib.sha256(full.read_bytes()).hexdigest()
            link=Path(directory)/'report.json';link.symlink_to(full)
            hard=Path(directory)/'hard.json';os.link(full,hard)
            for target in [None,Path('docs/ocaml-guide-validation.json'),full,link,hard]:
                with self.subTest(target=target):
                    command=[sys.executable,str(fixture/'scripts/validate_ocaml_guide.py'),'--lesson','first-program']
                    if target:command+=['--report',str(target)]
                    result=run_owned(command,cwd=fixture,timeout=10)
                    self.assertEqual(result.returncode,2,result.stderr)
                    self.assertEqual(hashlib.sha256(full.read_bytes()).hexdigest(),before)

    def test_committed_receipt_matches_current_inputs(self):
        # Fails when guide content changes without a re-validated, fully passing receipt.
        from validate_ocaml_guide import input_digests
        receipt=json.loads((ROOT/'docs/ocaml-guide-validation.json').read_text())
        self.assertIsNone(receipt['selectedLessons'])
        self.assertEqual(receipt['failed'],0)
        self.assertEqual(receipt['passed'],receipt['total'])
        self.assertEqual(receipt['inputSHA256'],input_digests(),'content changed since the committed receipt; rerun scripts/validate_ocaml_guide.py')


if __name__=='__main__':unittest.main()
