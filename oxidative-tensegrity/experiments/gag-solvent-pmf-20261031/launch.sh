#!/usr/bin/env bash
# Host-side launcher on the GPU box. Never provisions, stops or deletes a VM.
#   bash launch.sh quick     # 3-minute plumbing check
#   bash launch.sh full      # production (deadline 3.5 h)
# Network is used only here, on the host, to fetch the digest-pinned image and the hash-locked wheels.
set -euo pipefail
MODE=${1:-quick}
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE='python@sha256:78c6833ca878fd221957db5d580f7f2e9e31265b38656e97368caf23f12e24c8'  # same image Codex's approved OpenMM runs used
WHEELS=$HOME/gag-pmf-wheels
OUT=$HOME/gag-pmf-results-$MODE
mkdir -p "$WHEELS" "$OUT"
sudo docker pull "$IMAGE" >/dev/null
python3 - "$HERE/lock.json" "$WHEELS" <<'EOF'
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
DEADLINE=$(( $(date +%s) + ${DEADLINE_S:-$([ "$MODE" = full ] && echo 12600 || echo 600)} ))
ARGS="--out /results --workers 14"; [ "$MODE" = quick ] && ARGS="$ARGS --quick --workers 4"
NAME=gag-pmf-$MODE
sudo docker rm -f "$NAME" >/dev/null 2>&1 || true
sudo docker create --name "$NAME" --pull never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user "$(id -u):$(id -g)" --cpus 14 --memory 64g --pids-limit 512 --shm-size 1g \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=1g,mode=1777 --tmpfs /runtime:rw,exec,nosuid,nodev,size=3g,mode=1777 \
  --gpus all --mount "type=bind,src=$HERE,dst=/project,readonly" --mount "type=bind,src=$WHEELS,dst=/wheels,readonly" \
  --mount "type=bind,src=$OUT,dst=/results" --workdir /project --entrypoint /usr/bin/env "$IMAGE" -i \
  PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 OMP_NUM_THREADS=1 OPENMM_CPU_THREADS=1 CUDA_CACHE_PATH=/tmp/cuda-cache \
  PMF_DEADLINE_UNIX=$DEADLINE /usr/local/bin/python3 -I /project/entry.py $ARGS >/dev/null
sudo docker start --attach "$NAME" > "$OUT/container.log" 2>&1 || true
sudo docker inspect "$NAME" --format '{{json .State}}' > "$OUT/container-state.json"
sudo docker rm "$NAME" >/dev/null
echo "exit: $(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["ExitCode"])' "$OUT/container-state.json")"
