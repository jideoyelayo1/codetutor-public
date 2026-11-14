#!/bin/bash
set -euo pipefail
test "$(uname -s)" = Linux && test "$(uname -m)" = x86_64
PREFIX="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/leanprover/lean4/releases/download/v4.35.0/lean-4.35.0-linux.tar.zst \
  -o "$WORK/lean.tar.zst"
echo '7289597a44543246c9227b8cae501767e095ce17f6d448b95fc4a8dc97268f6d  '"$WORK/lean.tar.zst" | sha256sum --check -
tar --zstd -xf "$WORK/lean.tar.zst" --strip-components=1 -C "$PREFIX"
"$PREFIX/bin/lean" --version
