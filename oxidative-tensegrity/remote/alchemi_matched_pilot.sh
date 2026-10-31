#!/usr/bin/env bash
# Bounded conformer sensitivity pilot; molecular proxies only, no network overrides.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results
if [[ ${1:-} == setup ]]; then
  python -m venv /venv
  /venv/bin/pip install 'pip==24.3.1' 'uv==0.5.11'
  /venv/bin/uv pip install --python /venv/bin/python 'nvalchemi-toolkit[cu13,mace] @ git+https://github.com/NVIDIA/nvalchemi-toolkit@84fe8e8fb8fab54863eea8f138722c7ab434966a' 'rdkit==2024.9.6' 'ase==3.24.0'
  /venv/bin/python -c 'from alchemi_crosslinks import resolve_checkpoint; print(resolve_checkpoint("mace-off:medium"))'
  /venv/bin/pip freeze > results/environment.txt
  exit
fi
for seed in 101 102 103; do
  /venv/bin/python -u alchemi_crosslinks.py --device cuda --model mace-off:medium --seed "$seed" --chem-per-batch 1 --n-strain 9 --steps 3000 --fmax 0.02 --out "results/conformer_${seed}.json"
done
