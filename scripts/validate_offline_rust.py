"""Verify actual packaged Rust pages, assets and geometry against their source snapshot."""
import argparse
import hashlib
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from prepare_offline_rust import DOCS, ROOT


class Inventory(HTMLParser):
    def __init__(self):
        super().__init__(); self.svg=[]; self.paths=[]; self.links=[]
        self.images=[]; self.alternatives=0; self.active=[]
    def handle_starttag(self, tag, attributes):
        fields=dict(attributes)
        if tag=='svg': self.svg.append(fields.get('viewbox'))
        if tag=='path': self.paths.append(fields.get('d'))
        if tag=='img': self.images.append(fields.get('src',''))
        if fields.get('class')=='image-alternative': self.alternatives+=1
        for key in ['href','xlink:href']:
            if key in fields: self.links.append(fields[key])
        if tag in ['script','iframe','object','embed']: self.active.append(tag)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docs',type=Path,default=DOCS)
    parser.add_argument('--resources',type=Path,default=ROOT/'CodingTeacher/OfflineReferenceResources')
    args=parser.parse_args(); root=args.resources
    catalog=json.loads((root/'offline-reference-catalog.json').read_text())
    audit=json.loads((ROOT/'docs/offline-rust-coverage.json').read_text())
    pages=[p for b in catalog['books'] for p in b['pages']]
    audited={p['id']:p for b in audit['documents'] for p in b['pages']}
    totals=dict(pages=0,headings=0,inlineSVGs=0,inlineImages=0,remoteVersionBadgesAsText=0)
    for book in catalog['books']:
        assert (root/book['licenseFilename']).read_bytes()==(ROOT/'scripts/reference-licenses'/('rust-'+book['id'].removeprefix('rust-')+'-MIT.txt')).read_bytes()
    for page in pages:
        original=(args.docs/page['relativePath']).read_bytes()
        packaged=(root/page['filename']).read_bytes()
        assert hashlib.sha256(original).hexdigest()==page['originalSHA256'],page['id']
        assert hashlib.sha256(packaged).hexdigest()==page['packagedSHA256']==audited[page['id']]['packagedSHA256'],page['id']
        before=Inventory(); before.feed(re.search(r'<main>(.*?)</main>',original.decode(),re.S).group(1))
        after=Inventory(); after.feed(packaged.decode())
        assert before.svg==after.svg and before.paths==after.paths,('Geometry mismatch',page['id'])
        assert not after.active,('Active content',page['id'])
        assert all(src.startswith('data:image/') for src in after.images),('Unbundled image',page['id'])
        assert len(before.images)==len(after.images)+after.alternatives,('Lost image information',page['id'])
        for link in after.links:
            if link.startswith('ref-'): assert (root/link.split('#')[0]).is_file(),('Broken offline link',page['id'],link)
            assert not link.lower().startswith(('javascript:', 'data:')),('Active link',page['id'])
        totals['pages']+=1;totals['headings']+=len(page['headings']);totals['inlineSVGs']+=len(after.svg)
        totals['inlineImages']+=len(after.images);totals['remoteVersionBadgesAsText']+=after.alternatives
    report=dict(checked=datetime.now(timezone.utc).isoformat(),version=catalog['version'],books=len(catalog['books']),passed=True,
                **totals,geometryAndHashesMatch=True,allPracticeAdapted=False,
                scope='Source and packaged file/asset/geometry checks only; not all-page visual QA or executable example validation')
    (ROOT/'docs/offline-rust-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
