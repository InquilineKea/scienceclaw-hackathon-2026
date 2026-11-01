#!/usr/bin/env bash
# Collagen network -> organoid gene expression (run_organoid.py) on a disposable Brev GPU box.
#   bash remote/brev_organoid.sh smoke      # ~minutes, checks the pipeline
#   bash remote/brev_organoid.sh gpu        # full sweep
# Outputs: results/organoid/<profile>/ (copy back with brev copy).  Never run on the personal Mac.
set -euo pipefail
cd "$(dirname "$0")/.."
PROFILE="${1:-smoke}"
VENV="${VENV:-$HOME/oxt-venv}"
nvidia-smi --query-gpu=name,memory.total --format=csv
if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade "pip==24.3.1"
  # exact versions, all published > 1 year ago (same pins as remote/gpu_run.sh, plus tabulate for markdown)
  "$VENV/bin/python" -m pip install "numpy==1.26.4" "scipy==1.14.1" "pandas==2.2.3" "matplotlib==3.9.2" \
      "tabulate==0.9.0"
  "$VENV/bin/python" -m pip install "torch==2.5.1" --index-url https://download.pytorch.org/whl/cu124
fi
"$VENV/bin/python" -c "import torch; print('torch', torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
"$VENV/bin/python" run_organoid.py --profile "$PROFILE" --device cuda 2>&1 | tee "results/organoid_${PROFILE}.log"
