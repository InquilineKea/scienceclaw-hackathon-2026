#!/usr/bin/env bash
# Conformer ensemble for the B1 crosslink scan: MACE-OFF on every GPU, several RDKit seeds per GPU at once.
#   SEEDS="101 102 ..." PER_GPU=3 bash remote/brev_ensemble.sh      (from ~/oxt on a Brev GPU box)
# Each seed writes results/alchemi_ensemble/mace_off_s<seed>.json as soon as it finishes.
set -euo pipefail
cd "$(dirname "$0")/.."
COMMIT=84fe8e8fb8fab54863eea8f138722c7ab434966a   # user-approved 2026-10-30
if [ -z "${IN_CONTAINER:-}" ]; then
  exec docker run --rm --device nvidia.com/gpu=all -e IN_CONTAINER=1 -e SEEDS -e PER_GPU -e MODEL -v "$PWD":/work -w /work \
    -v oxt-alchemi-venv:/root/alchemi-venv -v oxt-cache:/root/.cache python:3.12.7-bookworm bash remote/brev_ensemble.sh
fi
if [ ! -x ~/alchemi-venv/bin/python ]; then
  python3 -m venv ~/alchemi-venv
  ~/alchemi-venv/bin/pip install -q "pip==24.3.1" "uv==0.5.11"
  ~/alchemi-venv/bin/uv pip install --python ~/alchemi-venv/bin/python \
    "nvalchemi-toolkit[cu13,mace] @ git+https://github.com/NVIDIA/nvalchemi-toolkit@${COMMIT}" \
    "aimnet==0.2.5" "rdkit==2024.9.6" "ase==3.24.0"
fi
. ~/alchemi-venv/bin/activate
MODEL="${MODEL:-mace-off:medium}"
NG=$(nvidia-smi -L | wc -l); PER_GPU="${PER_GPU:-3}"
mkdir -p results/alchemi_ensemble
i=0
for s in ${SEEDS:-101 102 103 104 105 106 107 108 109 110 111 112}; do
  out=results/alchemi_ensemble/${MODEL%%:*}_s$s.json
  [ -s "$out" ] && continue
  g=$(( i % NG ))
  CUDA_VISIBLE_DEVICES=$g python -W ignore alchemi_crosslinks.py --model "$MODEL" --device cuda --steps 3000 \
    --fmax 0.02 --seed "$s" --out "$out" > "results/alchemi_ensemble/${MODEL%%:*}_s$s.log" 2>&1 &
  i=$(( i + 1 ))
  if (( i % (NG * PER_GPU) == 0 )); then wait; fi
done
wait
echo "ENSEMBLE DONE"
