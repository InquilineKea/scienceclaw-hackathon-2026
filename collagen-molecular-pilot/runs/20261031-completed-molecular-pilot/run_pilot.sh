#!/usr/bin/env bash
# Run on the EXISTING Brev VM, after explicit approval of SECURITY_REVIEW.md.
# No provisioning, package installation, downloading, or modification of other jobs.
set -euo pipefail
cd -- "$(dirname -- "$0")"
DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  sudo -n docker info >/dev/null
  DOCKER=(sudo -n docker)
fi
if [ "${APPROVED_ISOLATED_PILOT:-}" != "yes" ]; then
  echo 'Requires explicit user approval after the security review.' >&2
  exit 64
fi
if nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q '[0-9]'; then
  if [ "${ALLOW_GPU_SHARING:-}" != "yes" ]; then
    echo 'GPU is in use; existing jobs were left untouched. Retry when it is free.' >&2
    exit 75
  fi
  free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1)
  if [ "$free_mib" -lt 8192 ]; then
    echo 'GPU sharing was authorized, but less than 8 GiB is free. Refusing to start.' >&2
    exit 75
  fi
fi
job="collagen-fragment-pilot-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "runs/$job"
out="$(pwd)/runs/$job"
image='python@sha256:78c6833ca878fd221957db5d580f7f2e9e31265b38656e97368caf23f12e24c8'
cleanup() { "${DOCKER[@]}" rm -f "$job" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
printf '%s\n' "$job" > "$out/job-label.txt"
printf 'GPU sharing authorized: %s\n' "${ALLOW_GPU_SHARING:-no}" > "$out/scheduling.txt"
date -u +%FT%TZ > "$out/started.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu --format=csv > "$out/gpu-before.csv"
set +e
timeout --signal=TERM --kill-after=10 600 "${DOCKER[@]}" run --name "$job" --pull never \
  --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --user "$(id -u):$(id -g)" --pids-limit 256 --memory 6g --cpus 2 \
  --device nvidia.com/gpu=0 \
  --tmpfs /tmp:rw,exec,nosuid,nodev,size=2g,mode=1777 \
  --mount "type=bind,src=$(pwd)/pilot.py,dst=/app/pilot.py,readonly" \
  --mount "type=bind,src=$out,dst=/out" \
  --mount type=volume,src=oxt-alchemi-venv,dst=/opt/venv,readonly \
  --mount type=volume,src=oxt-cache,dst=/models,readonly \
  -e HOME=/tmp -e XDG_CACHE_HOME=/tmp/cache -e MPLCONFIGDIR=/tmp/matplotlib \
  -e CUDA_CACHE_PATH=/tmp/cuda-cache -e NUMBA_CACHE_DIR=/tmp/numba-cache \
  -e PYTHONDONTWRITEBYTECODE=1 -e OMP_NUM_THREADS=2 -e "PILOT_JOB_LABEL=$job" \
  "$image" /opt/venv/bin/python -u /app/pilot.py --out /out \
  > "$out/console.log" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" > "$out/exit-code.txt"
date -u +%FT%TZ > "$out/finished.txt"
"${DOCKER[@]}" inspect "$job" --format '{{.Id}} {{.State.ExitCode}} {{.State.OOMKilled}} {{.State.StartedAt}} {{.State.FinishedAt}}' > "$out/container-execution.txt" || true
nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv > "$out/gpu-after.csv"
cat "$out/console.log"
exit "$rc"
