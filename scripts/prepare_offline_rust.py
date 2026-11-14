"""Package the licensed Rust 1.99 manuals for an offline, script-free app reader.

Uses the official rust-docs component. Keeps full source payloads in an ignored
resource folder, while committing a metadata-only section/practice coverage audit.
No code example or embedded instruction is executed by this packager.
"""
import argparse
import base64
import hashlib
from datetime import datetime, timezone
from html import escape, unescape
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT/'.build/toolchains/rustup/toolchains/1.99.0-aarch64-apple-darwin/share/doc/rust/html'
BOOKS = [
    ('rust-book','book','The Rust Programming Language','Steve Klabnik, Carol Nichols, Chris Krycho and the Rust community','book'),
    ('rust-example','rust-by-example','Rust by Example','Jorge Aparicio and the Rust community','example'),
    ('rust-reference','reference','The Rust Reference','The Rust Project Developers and contributors','reference'),
    ('rust-cargo','cargo','The Cargo Book','The Rust Project Developers and contributors','cargo'),
    ('rust-edition','edition-guide','The Rust Edition Guide','The Rust Project Developers and contributors','edition'),
    ('rust-nomicon','nomicon','The Rustonomicon','The Rust Project Developers and contributors','nomicon'),
]
CSS = '''
html { color-scheme: light dark; -webkit-text-size-adjust:100%; }
body { font: 18px/1.65 -apple-system, sans-serif; margin:22px; overflow-wrap:anywhere; }
body { font: -apple-system-body; line-height:1.65; }
h1,h2,h3,h4,h5,h6 { line-height:1.3; margin-top:1.5em; }
a { color:#368cba; } pre { white-space:pre; overflow-x:auto; padding:16px; border-radius:12px; background:#80808018; }
code { font: .9em/1.6 ui-monospace, Menlo, monospace; } p code,li code { overflow-wrap:anywhere; }
img,svg { max-width:100%; height:auto; } table { display:block; overflow:auto; border-collapse:collapse; }
td,th { border:1px solid #8887; padding:8px; } blockquote { border-left:3px solid #8887; padding-left:16px; margin-left:0; }
.hidden { display:none; } .header { color:inherit; text-decoration:none; } footer { margin-top:40px; border-top:1px solid #8885; font-size:14px; }
svg.railroad { background:#fff; color:#111; padding:8px; border-radius:10px; }
svg.railroad path { stroke:#111; stroke-width:2; fill:none; }
svg.railroad text { fill:#111; font:14px monospace; text-anchor:middle; }
svg.railroad rect { stroke:#111; stroke-width:2; fill:#e7f1f6; }
svg.railroad circle { stroke:#111; fill:#111; }
svg.railroad .railroad_canvas { fill:#fff; stroke:none; }
.railroad-production { overflow-x:auto; width:100% !important; }
.railroad-production svg.railroad { max-width:none; }
'''


class TOC(HTMLParser):
    def __init__(self): super().__init__(); self.items=[]; self.href=None; self.text=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.href=dict(attrs).get('href'); self.text=[]
    def handle_data(self, data):
        if self.href is not None: self.text.append(data)
    def handle_endtag(self, tag):
        if tag=='a' and self.href is not None:
            if '.html' in self.href and not urlsplit(self.href).scheme:
                self.items.append((self.href.split('#')[0],''.join(self.text).strip()))
            self.href=None


class Content(HTMLParser):
    """Retain semantic HTML, remove active content, inline local pictures, rewrite links."""
    BLOCKED={'script','style','iframe','object','embed','audio','video','form','button','input','link','meta'}
    BLOCKED_VOID={'input','link','meta','embed'}
    VOID={'img','br','hr','wbr'}
    SVG_ATTRIBUTES={'viewbox','preserveaspectratio','width','height','d','points','x','y','x1','x2','y1','y2','cx','cy','r','rx','ry','dx','dy','transform','fill','fill-opacity','fill-rule','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-opacity','opacity','text-anchor','font-size','font-family','dominant-baseline','xmlns','xmlns:xlink','role','pathlength'}
    SVG_CASE={'viewbox':'viewBox','preserveaspectratio':'preserveAspectRatio','pathlength':'pathLength'}
    def __init__(self, source, docs, names):
        super().__init__(convert_charrefs=False)
        self.source=source;self.docs=docs;self.names=names;self.parts=[];self.skip=[]
        self.headings=[];self.heading=None;self.heading_text=[];self.word_text=[]
    def link(self, value):
        parsed=urlsplit(value)
        if parsed.scheme or value.startswith('//'):
            if parsed.hostname=='doc.rust-lang.org' and parsed.scheme in ['', 'https', 'http']:
                path=unquote(parsed.path).lstrip('/')
                for prefix in ['1.99.0/', 'stable/', 'latest/']:
                    if path.startswith(prefix): path=path[len(prefix):];break
                target=(self.docs/path).resolve()
                if target in self.names: return self.names[target]+('#'+parsed.fragment if parsed.fragment else '')
            return value if parsed.scheme in ['https','http','mailto'] else '#'
        if not parsed.path: return value
        target=(self.source.parent/unquote(parsed.path)).resolve()
        if target in self.names: return self.names[target]+('#'+parsed.fragment if parsed.fragment else '')
        try: relative=target.relative_to(self.docs)
        except ValueError: return '#'
        return 'https://doc.rust-lang.org/1.99.0/'+relative.as_posix()+('#'+parsed.fragment if parsed.fragment else '')
    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag in self.BLOCKED and tag not in self.BLOCKED_VOID: self.skip.append(tag)
            return
        if tag in self.BLOCKED:
            if tag not in ['input','link','meta','embed']: self.skip.append(tag)
            return
        attributes=dict(attrs)
        if tag=='img' and urlsplit(attributes.get('src','')).scheme:
            # Edition-guide badges are remote images; their alt text carries the same information offline.
            alternative=attributes.get('alt','')
            if not alternative: raise ValueError(f'Remote image has no offline alternative: {self.source}')
            self.parts.append('<span class="image-alternative">'+escape(alternative)+'</span>')
            return
        if tag=='svg' and 'railroad' in attributes.get('class',''):
            box=attributes.get('viewbox','').split()
            if len(box)==4:
                if 'width' not in attributes: attrs=attrs+[('width',box[2])]
                if 'height' not in attributes: attrs=attrs+[('height',box[3])]
        fields=[]
        for key,value in attrs:
            if key=='style':
                if value and not re.search(r'url\s*\(|expression\s*\(|@import|binding',value,re.I): fields.append('style="'+escape(value,quote=True)+'"')
                continue
            if key=='xlink:href':
                fields.append('xlink:href="'+escape(self.link(value or ''),quote=True)+'"')
                continue
            if key not in ['id','class','href','src','alt','title','colspan','rowspan','open','lang','aria-label'] and key not in self.SVG_ATTRIBUTES: continue
            if key=='href': value=self.link(value or '')
            if key=='src':
                path=(self.source.parent/unquote(urlsplit(value or '').path)).resolve()
                try: path.relative_to(self.docs)
                except ValueError: continue
                if not path.is_file(): raise ValueError(f'Image unavailable: {path}')
                mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
                if not mime.startswith('image/'): continue
                value='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
            key=self.SVG_CASE.get(key,key)
            fields.append(key if value is None else f'{key}="{escape(value,quote=True)}"')
        if re.fullmatch(r'h[1-6]',tag):
            self.heading=dict(attrs).get('id','');self.heading_text=[]
        self.parts.append('<'+tag+(' '+' '.join(fields) if fields else '')+'>')
    def handle_endtag(self, tag):
        if self.skip:
            if tag==self.skip[-1]: self.skip.pop()
            return
        if tag in self.BLOCKED or tag in self.VOID: return
        self.parts.append('</'+tag+'>')
        if re.fullmatch(r'h[1-6]',tag) and self.heading is not None:
            self.headings.append({'anchor':self.heading,'title':''.join(self.heading_text).strip()});self.heading=None
    def handle_data(self, data):
        if self.skip: return
        self.parts.append(escape(data));self.word_text.append(data)
        if self.heading is not None: self.heading_text.append(data)
    def handle_entityref(self, name): self.handle_data(unescape('&'+name+';'))
    def handle_charref(self, name): self.handle_data(unescape('&#'+name+';'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--docs',type=Path,default=DOCS)
    args=parser.parse_args();docs=args.docs.resolve();output=ROOT/'CodingTeacher/OfflineReferenceResources'
    output.mkdir(parents=True,exist_ok=True)
    records=[];names={};books=[]
    for identifier,directory,title,authors,license_key in BOOKS:
        toc=TOC();toc.feed((docs/directory/'toc.html').read_text())
        seen=set();pages=[]
        for relative,label in toc.items:
            path=(docs/directory/relative).resolve()
            if path in seen: continue
            path.relative_to(docs);seen.add(path)
            if path.name in ['print.html','toc.html']: continue
            if not path.is_file(): raise ValueError(f'TOC page unavailable: {path}')
            filename='ref-'+identifier+'-'+hashlib.sha256(relative.encode()).hexdigest()[:16]+'.html'
            names[path]=filename
            record={'id':identifier+':'+relative,'bookID':identifier,'title':label,'filename':filename,
                    'sourceURL':'https://doc.rust-lang.org/1.99.0/'+directory+'/'+relative,'relativePath':directory+'/'+relative,'originalSHA256':hashlib.sha256(path.read_bytes()).hexdigest()}
            records.append((path,record));pages.append(record)
        # mdBook TOCs often omit the landing page, so alias it (and its directory) to the first page.
        if pages:
            names.setdefault(docs/directory/'index.html',pages[0]['filename'])
            names.setdefault(docs/directory,pages[0]['filename'])
        license_name='ref-'+identifier+'-license.txt'
        license_path=ROOT/'scripts/reference-licenses'/('rust-'+license_key+'-MIT.txt')
        (output/license_name).write_bytes(license_path.read_bytes())
        books.append({'id':identifier,'title':title,'authors':authors,'version':'Rust 1.99.0','license':'MIT','licenseFilename':license_name,'pages':pages})
    for source,record in records:
        original=source.read_text();match=re.search(r'<main>(.*?)</main>',original,re.S)
        if not match: raise ValueError(f'Missing main content: {source}')
        content=Content(source,docs,names);content.feed(match.group(1))
        record['headings']=content.headings;record['wordCount']=len(' '.join(content.word_text).split())
        html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+CSS+'</style><title>'+escape(record['title'])+'</title></head><body>'+''.join(content.parts)+'<footer>Source: '+escape(record['sourceURL'])+'<br>Rust 1.99.0 documentation. See the in-app source license and contributor attribution.</footer></body></html>'
        (output/record['filename']).write_text(html)
        record['packagedSHA256']=hashlib.sha256(html.encode()).hexdigest()
    catalog={'schemaVersion':1,'version':'Rust 1.99.0','books':books}
    (output/'offline-reference-catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    # Metadata/locators only: complete reading access is not complete practice adaptation.
    content=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    for book in books:
        for page in book['pages']:
            path=page['relativePath']
            page['lessonIDs']=[l['id'] for l in content['lessons'] if any(urlsplit(url).path.endswith('/'+path) for url in [l['sourceURL']]+[r['url'] for r in l.get('reading',[]) if r.get('url')])]
            page['readingPackaged']=True;page['fullyAdapted']=False
    audit={'checked':datetime.now(timezone.utc).isoformat(),'version':'Rust 1.99.0','documents':books,
           'pageCount':len(records),'headingCount':sum(len(r['headings']) for _,r in records),
           'readingAccessComplete':True,'allPracticeAdapted':False,
           'scope':'All TOC-linked pages of six official manuals; source text/assets stay in ignored resources; authored practice depth remains audited separately'}
    (ROOT/'docs/offline-rust-coverage.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'books':len(books),'pages':len(records),'headings':audit['headingCount'],
                     'bytes':sum(p.stat().st_size for p in output.iterdir() if p.is_file())},indent=2))


if __name__=='__main__': main()
