#!/usr/bin/env bash
# Run ONLY after the user approves the reviewed GROMACS runtime, on an isolated host.
# This script does not install software, authenticate, create cloud resources, or use network.
set -euo pipefail
umask 077
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
GMX_BIN="${GMX_BIN:-gmx}"
MODE="${MODE:-gpu}"
THREADS="${THREADS:-4}"
case "$MODE" in gpu|cpu) ;; *) echo 'MODE must be gpu or cpu' >&2; exit 2;; esac
case "$THREADS" in 1|2|4|8) ;; *) echo 'THREADS must be 1, 2, 4, or 8' >&2; exit 2;; esac
command -v "$GMX_BIN" >/dev/null || { echo 'Approved GROMACS runtime required' >&2; exit 2; }
command -v timeout >/dev/null || { echo 'GNU timeout required on the Linux runner' >&2; exit 2; }
# Fail rather than mix results from repeated attempts.
RUN_DIR="$ROOT/runs/ppg9-${MODE}-seed104729"
mkdir -p "$ROOT/runs"
mkdir "$RUN_DIR"
cd "$RUN_DIR"
export GMX_MAXBACKUP=-1
unset GMXLIB GMXDATA
sha256sum "$(command -v "$GMX_BIN")" > gromacs-binary.sha256
"$GMX_BIN" --version > gromacs-version.txt 2>&1
if ! grep -Eq 'GROMACS version:.*2025\.3' gromacs-version.txt; then
    echo 'Review/version mismatch: this pilot targets GROMACS 2025.3' >&2; exit 2
fi
if [ "$MODE" = gpu ]; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > gpu.txt
fi
cp "$ROOT/inputs/collagen_ppg9.pdb" input.pdb
cp "$ROOT"/mdp/*.mdp .
# Standard GROMACS AMBER99SB-ILDN; intentionally NOT ColBuilder's modified force field.
# PRO/GLY only, default charged termini. TER and chain identifiers keep strands separate.
"$GMX_BIN" pdb2gmx -f input.pdb -o processed.gro -p topol.top -i posre.itp \
    -ff amber99sb-ildn -water tip3p -ignh -chainsep id_or_ter -merge no \
    > pdb2gmx.log 2>&1
"$GMX_BIN" editconf -f processed.gro -o boxed.gro -c -d 1.2 -bt triclinic > editconf.log 2>&1
"$GMX_BIN" solvate -cp boxed.gro -cs spc216.gro -p topol.top -o solvated.gro > solvate.log 2>&1
# spc216.gro supplies only seed coordinates. The topology uses TIP3P parameters and SETTLE geometry.
# Three zwitterionic PRO/GLY chains are neutral; this pilot deliberately has no added salt.
"$GMX_BIN" grompp -f em.mdp -c solvated.gro -p topol.top -o em.tpr \
    -pp em.processed.top -po em.actual.mdp -maxwarn 0 > em.grompp.log 2>&1
timeout --signal=TERM --kill-after=15s 300s "$GMX_BIN" mdrun -deffnm em \
    -ntmpi 1 -ntomp "$THREADS" -nb cpu > em.console.log 2>&1
python3 "$ROOT/verify_run.py" --em-only "$RUN_DIR"

for stage in nvt npt sample; do
    case "$stage" in
        nvt) previous=em; extra=(-r em.gro) ;;
        npt) previous=nvt; extra=(-r em.gro -t nvt.cpt) ;;
        sample) previous=npt; extra=(-t npt.cpt) ;;
    esac
    "$GMX_BIN" grompp -f "$stage.mdp" -c "$previous.gro" -p topol.top \
        -o "$stage.tpr" -pp "$stage.processed.top" -po "$stage.actual.mdp" \
        -maxwarn 0 "${extra[@]}" > "$stage.grompp.log" 2>&1
    # Five minutes per stage; the cloud bootstrap also limits the complete child process.
    timeout --signal=TERM --kill-after=15s 300s "$GMX_BIN" mdrun -deffnm "$stage" \
        -ntmpi 1 -ntomp "$THREADS" -nb "$MODE" -pme cpu -bonded cpu -update cpu \
        > "$stage.console.log" 2>&1
done
"$GMX_BIN" check -f sample.xtc > trajectory-check.txt 2>&1
"$GMX_BIN" dump -s sample.tpr > sample.tpr.txt 2>&1
printf 'Temperature\nPotential\nPressure\nDensity\n0\n' | \
    "$GMX_BIN" energy -f sample.edr -o sample-energy.xvg > energy-summary.txt 2>&1
printf 'Backbone\nBackbone\n' | "$GMX_BIN" rms -s sample.tpr -f sample.xtc \
    -o backbone-rmsd.xvg -tu ps > rmsd-analysis.txt 2>&1
python3 "$ROOT/verify_run.py" "$RUN_DIR" --mode "$MODE"
