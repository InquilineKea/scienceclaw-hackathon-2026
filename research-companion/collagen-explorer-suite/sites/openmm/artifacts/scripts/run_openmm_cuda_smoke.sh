#!/usr/bin/env bash
# Run in an execution context with authorized GPU and HTTPS access.
set -euo pipefail

project_root="$(dirname -- "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")")"
venv_python="$project_root/.venv/bin/python"
run_tag="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$project_root/evidence" "$project_root/downloads" "$project_root/results"
exec > >(tee "$project_root/evidence/openmm_cuda_${run_tag}.log") 2>&1

hostname
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv,noheader
"$venv_python" - <<'PY'
import ctypes
import json
import platform
import sys

cuda = ctypes.CDLL("libcuda.so.1")
cuda.cuInit.argtypes = [ctypes.c_uint]
cuda.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
rc = cuda.cuInit(0)
count = ctypes.c_int()
count_rc = cuda.cuDeviceGetCount(ctypes.byref(count)) if rc == 0 else None
print(json.dumps({"hostname": platform.node(), "python": sys.executable,
                  "cuInit_returncode": rc, "count_returncode": count_rc,
                  "device_count": count.value}), flush=True)
if rc != 0 or count_rc != 0 or count.value < 1:
    raise SystemExit("CUDA initialization/device enumeration failed")
PY
curl --fail --silent --show-error --head --connect-timeout 10 --max-time 30 \
    https://pypi.org/simple/openmm/

if ! "$venv_python" -m pip --version; then
    curl --fail --location --silent --show-error --connect-timeout 10 --max-time 60 \
        https://bootstrap.pypa.io/get-pip.py --output "$project_root/downloads/get-pip.py"
    "$venv_python" "$project_root/downloads/get-pip.py"
fi

# OpenMM's documented CUDA extra includes the CUDA platform and its dependencies.
# https://docs.openmm.org/latest/userguide/application/01_getting_started.html
"$venv_python" -m pip install --only-binary=:all: 'openmm[cuda12]'
"$venv_python" -m pip freeze > "$project_root/evidence/openmm_cuda_${run_tag}_packages.txt"
"$venv_python" "$project_root/scripts/openmm_cuda_smoke.py" \
    --output "$project_root/results/openmm_cuda_${run_tag}.json"
