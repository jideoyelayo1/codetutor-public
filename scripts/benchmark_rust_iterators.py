"""Measure bundled eager/lazy search on one synthetic, preloaded text.

Trusted local code only. No timing threshold, allocator measurement, disk-I/O
benchmark, sandbox certification or general speedup claim.
"""
import datetime
import hashlib
import json
from pathlib import Path

from owned_process import run_owned

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / '.build/rust-iterator-benchmark'
TOOLCHAIN = ROOT / '.build/toolchains/rustup/toolchains/1.99.0-aarch64-apple-darwin/bin'

HARNESS = r'''
#[path = "base.rs"] mod base;
#[path = "answer.rs"] mod answer;
use std::{hint::black_box, time::Instant};

fn sample<F: FnMut() -> usize>(mut work: F) -> u128 {
    // Warm separately, then retain the median of seven fresh evaluations.
    black_box(work());
    let mut times = Vec::new();
    for _ in 0..7 {
        let started = Instant::now();
        black_box(work());
        times.push(started.elapsed().as_nanos());
    }
    times.sort_unstable();
    times[3]
}
fn main() {
    let text = "rust is safe; original spelling and bytes remain here\n".repeat(500_000);
    let query = black_box("rust");
    assert_eq!(base::search(query, &text).len(), 500_000);
    assert_eq!(answer::search(query, &text).count(), 500_000);
    assert_eq!(base::search(query, &text).first().copied(), answer::search(query, &text).next());
    let eager_first = sample(|| base::search(query, black_box(&text)).first().map_or(0, |s| s.len()));
    let lazy_first = sample(|| answer::search(query, black_box(&text)).next().map_or(0, |s| s.len()));
    let eager_all = sample(|| base::search(query, black_box(&text)).len());
    let lazy_all = sample(|| answer::search(query, black_box(&text)).count());
    println!("{{\"inputBytes\":{},\"lines\":500000,\"samples\":7,\"medianNanoseconds\":{{\"eagerFirst\":{},\"lazyFirst\":{},\"eagerAll\":{},\"lazyAll\":{}}}}}", text.len(), eager_first, lazy_first, eager_all, lazy_all);
}
'''


def main():
    curriculum_path = ROOT / 'CodingTeacher/curriculum.json'
    payload = curriculum_path.read_bytes()
    lesson = next(l for l in json.loads(payload)['lessons'] if l['id'] == 'guide.rust.iterator-cli-project')
    WORK.mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    for key, filename in [('projectFiles', 'base.rs'), ('projectSolutionFiles', 'answer.rs')]:
        code = next(f['content'] for f in lesson[key] if f['path'] == 'src/lib.rs')
        source_hashes[key] = hashlib.sha256(code.encode()).hexdigest()
        (WORK / filename).write_text(code)
    (WORK / 'main.rs').write_text(HARNESS)
    version = run_owned([str(TOOLCHAIN / 'rustc'), '--version']).stdout.strip()
    if not version.startswith('rustc 1.99.0 '):
        raise ValueError('Rust 1.99.0 required')
    compiled = run_owned([str(TOOLCHAIN / 'rustc'), '--edition=2024', '-O',
                          str(WORK / 'main.rs'), '-o', str(WORK / 'benchmark')], timeout=30)
    if compiled.returncode:
        raise RuntimeError(compiled.stderr)
    result = run_owned([str(WORK / 'benchmark')], timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr)
    if curriculum_path.read_bytes() != payload:
        raise ValueError('Curriculum changed during benchmark')
    report = dict(checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  compiler=version, optimization='rustc -O',
                  curriculumSHA256=hashlib.sha256(payload).hexdigest(),
                  librarySourceSHA256=source_hashes,
                  workload=json.loads(result.stdout),
                  scope='One synthetic preloaded all-match input on this Mac; median wall times, no threshold; excludes file reading, allocation accounting, peak memory, sparse matches and OS pipe scheduling')
    (ROOT / 'docs/rust-iterator-benchmark.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
