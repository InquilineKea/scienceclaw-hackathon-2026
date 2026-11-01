#!/usr/bin/env bash
# Run pymoo + sympy on the GCP VM in isolation. Executed by the sudo-capable `simfish` user on oxt-cpu32.
#   bash run_on_vm.sh STAGING_DIR [GENS]
# - wheels fetched on the host by hash (network only here), unpacked with --no-deps --require-hashes
# - code runs as a separate unprivileged user `moo` (cannot read /home/oxt/.gemini.key, mode 600)
#   inside a network namespace with no interfaces (unshare -n), reusing the oxt venv's numpy/scipy/torch read-only
set -euo pipefail
STAGE=$1; GENS=${2:-10}
sudo id moo >/dev/null 2>&1 || sudo useradd --system --create-home --home-dir /opt/moo-home --shell /usr/sbin/nologin moo
sudo mkdir -p /opt/moo-wheels /opt/moo-site /opt/moo-work
sudo chown "$USER" /opt/moo-wheels
python3 - "$STAGE/team/moo_env/lock.json" /opt/moo-wheels <<'EOF'
import hashlib, json, sys, urllib.request
from pathlib import Path
lock, dst = json.load(open(sys.argv[1])), Path(sys.argv[2])
for p in lock["packages"]:
    f = dst / p["filename"]
    if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest() != p["sha256"]:
        urllib.request.urlretrieve(p["url"], f)
    assert hashlib.sha256(f.read_bytes()).hexdigest() == p["sha256"], p["filename"]
print("wheels verified:", len(lock["packages"]))
EOF
sudo /home/oxt/v/bin/python3 -I -m pip install --quiet --disable-pip-version-check --no-index --no-deps --require-hashes \
  --no-cache-dir --find-links /opt/moo-wheels --target /opt/moo-site -r "$STAGE/team/moo_env/requirements.txt"
sudo rsync -a --delete "$STAGE/" /opt/moo-work/ot/
sudo chown -R moo:moo /opt/moo-work
sudo chmod -R a-w /opt/moo-site
cat > /tmp/moo_boot.py <<'EOF'
import runpy, sys
sys.path[:0] = ["/opt/moo-work/ot", "/opt/moo-site", "/home/oxt/v/lib/python3.11/site-packages"]
script = sys.argv[1]; sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
EOF
sudo install -o moo -m 0444 /tmp/moo_boot.py /opt/moo-work/boot.py
RUN="sudo unshare -n -- sudo -u moo env -i HOME=/opt/moo-home PATH=/usr/bin:/bin OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg"
cd /opt/moo-work/ot
$RUN /usr/bin/python3.11 -s /opt/moo-work/boot.py team/sympy_checks.py > /tmp/sympy.log 2>&1; echo "sympy exit $?"
$RUN /usr/bin/python3.11 -s /opt/moo-work/boot.py team/topo_pymoo.py run --gens "$GENS" --pop 28 --workers 28 --seed 77 > /tmp/pymoo.log 2>&1; echo "pymoo exit $?"
$RUN /usr/bin/python3.11 -s /opt/moo-work/boot.py team/topo_pymoo.py compare > /tmp/pymoo_compare.log 2>&1; echo "compare exit $?"
