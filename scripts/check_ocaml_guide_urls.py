"""Fetch every URL the OCaml guide cites or the source ledger lists and record the HTTP status.

This is a reachability check only: it shows a page exists on the day it ran, not that its content
still matches the lesson. Run it before a release; it needs network access and is not part of the offline tests.
"""
import concurrent.futures
import datetime
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_ocaml_source_ledger import ROOT, cited_urls

REPORT = ROOT / 'docs/ocaml-guide-url-check.json'


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'CodingTeacher-url-check'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return url, response.status
        except urllib.error.HTTPError as error:
            if error.code < 500:
                return url, error.code
        except (urllib.error.URLError, TimeoutError) as error:
            last = str(error)
    return url, last if 'last' in locals() else 'server error'


def main():
    ledger = json.loads((ROOT / 'scripts/ocaml_source_ledger.json').read_text())
    urls = set(cited_urls())
    urls |= {source['base'] + page['path'] for source in ledger['sources'] for page in source['pages']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        statuses = dict(pool.map(fetch, sorted(urls)))
    bad = {url: status for url, status in statuses.items() if status != 200}
    report = dict(checked=datetime.datetime.now(datetime.timezone.utc).isoformat(), urls=len(statuses),
                  ok=len(statuses) - len(bad), notOK=bad,
                  scope='Reachability only (HTTP 200 after redirects); page content was not compared with the lessons')
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
