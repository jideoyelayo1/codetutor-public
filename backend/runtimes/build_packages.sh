#!/bin/bash
set -euo pipefail
test "$(uname -s)" = Linux && test "$(uname -m)" = x86_64
mkdir -p /export
for record in 'python-ml:3.13.14' 'lean4:4.35.0'; do
    name="${record%:*}"
    version="${record#*:}"
    destination="/piston/packages/$name/$version"
    mkdir -p "$destination"
    cp -a "/recipes/$name/." "$destination/"
    bash "$destination/build.sh"
    python3 - "$destination" <<'PY'
import json, pathlib, subprocess, sys
p=pathlib.Path(sys.argv[1])
metadata=json.loads((p/'metadata.json').read_text())
metadata['build_platform']='docker-debian'
(p/'pkg-info.json').write_text(json.dumps(metadata)+'\n')
env=subprocess.check_output(['env','-i','PATH=/usr/local/bin:/usr/bin:/bin','bash','-c',
                             'cd "$1"; source ./environment; env','environment',str(p)],text=True)
excluded={'PWD','OLDPWD','SHLVL','_'}
(p/'.env').write_text(''.join(line+'\n' for line in sorted(env.splitlines()) if line.split('=',1)[0] not in excluded))
(p/'.ppman-installed').write_text('custom-package\n')
PY
    tar -C "$destination" -czf "/export/$name-$version.tar.gz" .
done
cd /export
sha256sum *.tar.gz > SHA256SUMS
printf '%s\n' "builder=$BUILD_IMAGE" > BUILD_IMAGE
