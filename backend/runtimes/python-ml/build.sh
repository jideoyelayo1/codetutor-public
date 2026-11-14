#!/bin/bash
set -euo pipefail
# Run inside the Linux builder only; the resulting tree is a Piston package.
test "$(uname -s)" = Linux && test "$(uname -m)" = x86_64
PREFIX="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git -C "$WORK" init -q
git -C "$WORK" remote add origin https://github.com/python/cpython
git -C "$WORK" fetch --depth=1 origin fd17997c3866d61e0e7bd8201b1d8f35b40a40bd
git -C "$WORK" checkout --detach -q FETCH_HEAD
cd "$WORK"
./configure --prefix="$PREFIX" --with-ensurepip=install
make -j2
make install
cd "$PREFIX"
bin/python3.13 -m pip install --require-hashes --only-binary=:all: -r requirements.lock
bin/python3.13 -m pip check
bin/python3.13 -c 'import numpy,pandas,sklearn,torch; assert torch.version.cuda is None'
# pip/ensurepip are build tools; learners receive no package installer.
rm -rf lib/python3.13/ensurepip lib/python3.13/site-packages/pip lib/python3.13/site-packages/pip-*.dist-info
rm -f bin/pip*
find lib -type d -name __pycache__ -prune -exec rm -rf '{}' +
