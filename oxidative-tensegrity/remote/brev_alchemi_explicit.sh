#!/usr/bin/env bash
# Explicit-solvent collagen-GAG binding PMF on a disposable CUDA box (Brev instance or Nebius VM). Never on the Mac.
#   bash remote/brev_alchemi_explicit.sh                 # the four glycation comparisons at DS-4S, full sampling
#   QUICK=1 bash remote/brev_alchemi_explicit.sh         # smoke profile (20 ps equil / 50 ps sample per window)
#   PAIRS="all" bash remote/brev_alchemi_explicit.sh     # all 4x3 collagen x GAG pairs (expensive)
# Outputs: results/alchemi_gag/collagen_gag_pmf.json  (+ .traces.npz if SAVE_TRACES=1). Copy them back yourself.
#
# Unlike the mesoscale sweep (pip + torch), this stage needs AmberTools' antechamber/sqm for AM1-BCC charges,
# which is conda-only -- so we use micromamba with pinned conda-forge packages (all mature, > 1 year published).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${OUT:-results/alchemi_gag/collagen_gag_pmf.json}"
ENV_DIR="${ENV_DIR:-/tmp/alchemi-explicit-env}"
PAIRS="${PAIRS:-Lys:DS-4S CML-Lys:DS-4S Arg:DS-4S MG-H1-Arg:DS-4S}"

nvidia-smi --query-gpu=name,memory.total --format=csv

# --- micromamba bootstrap (no system conda assumed) --------------------------------------------------------
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-/tmp/micromamba}"
if ! command -v micromamba >/dev/null 2>&1; then
  mkdir -p "$MAMBA_ROOT_PREFIX/bin"
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C "$MAMBA_ROOT_PREFIX" bin/micromamba
  export PATH="$MAMBA_ROOT_PREFIX/bin:$PATH"
fi
eval "$(micromamba shell hook --shell bash)"

# --- pinned, mature conda-forge toolchain ------------------------------------------------------------------
if [[ ! -d "$ENV_DIR" ]]; then
  micromamba create -y -p "$ENV_DIR" -c conda-forge \
    "python=3.11" \
    "openmm=8.1.1" \
    "openmmforcefields=0.12.0" \
    "openff-toolkit=0.16.2" \
    "ambertools=23.6" \
    "pymbar=4.0.3" \
    "rdkit=2024.03.5" \
    "numpy=1.26.4" \
    "cuda-version=12.4"
fi
micromamba activate "$ENV_DIR"

python - <<'EOF'
import openmm, openmm.version
print("openmm", openmm.version.version)
print("platforms:", [openmm.Platform.getPlatform(i).getName() for i in range(openmm.Platform.getNumPlatforms())])
EOF

ARGS=(--device CUDA --out "$OUT" --save-traces --pairs $PAIRS)
if [[ "${QUICK:-0}" == "1" ]]; then ARGS+=(--quick); fi
if [[ "${SAVE_TRACES:-1}" == "0" ]]; then ARGS=("${ARGS[@]/--save-traces}"); fi

python alchemi_collagen_gag_explicit.py "${ARGS[@]}"
echo "done: $OUT"
