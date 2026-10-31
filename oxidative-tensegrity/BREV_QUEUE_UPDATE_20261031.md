# Brev queue update 2026-10-31 (Hermes) — merge into AGENTS.md

Direct edits to `AGENTS.md` were blocked by this session's protected-file write guard, so the
queue update is recorded here for the maintainer to apply verbatim.

## Brev job queue rows (replace the open B2/B3 rows)

| ID | Job | Command (on the Brev box, from this folder) | Outputs to bring back | Claimed by | Status |
|---|---|---|---|---|---|
| B2 | Large network/tissue/cell sweep (48x48, 8 seeds) | same command as B1 (runs after it), or `python run_sweep.py --profile gpu --device cuda` | `results/gpu/` | Hermes, Brev H100 | running (launched 2026-10-31; log `~/oxt-run.log` on `junction-organoid-h100-20261031`, container `python:3.12.7-bookworm` + `remote/gpu_run.sh`, torch 2.5.1+cu124, "[network] 4680 systems in 74 batches") |
| B3 | LAMMPS oscillatory shear, G' and G'' (healthy vs oxidised Col I / VII) | `python remote/make_lammps_inputs.py 32 && cd remote/lammps && for f in *.in; do lmp -in $f; done` (LAMMPS from conda-forge, pinned) | `remote/lammps/*_stress.txt` | Hermes, Brev L40S | done |

## Findings to append under "Findings from Brev jobs"

- B3 (Hermes, Brev L40S `collagen-md-l40s-20261031`): LAMMPS 2024.08.29 (conda-forge, micromamba 1.5.10, pinned `python:3.12.7-bookworm` container; bookworm needed because the conda-forge build requires GLIBC ≥ 2.34). Decks regenerated on the box (W=32, seed 42) and are byte-identical to the committed ones; all 6 ran to completion ("Dangerous builds = 0"). fit_viscoelastic (period 200, first cycle discarded): oxidative crosslinking raises G' and G'' in both collagen types; G' Col I none/iso/aniso = 0.0554/0.1289/0.0812 (iso 2.33×, aniso 1.46× healthy), Col VII = 0.0224/0.0383/0.0293 (iso 1.71×, aniso 1.31×); G'' Col I = 0.252/0.422/0.319, Col VII = 0.0833/0.154/0.0990; tan δ ≈ 3.3–4.6 everywhere (loss-dominated at ω = 2π/200 with Langevin damp 1.0, i.e. strongly dissipative regime). Col I ~2.5× stiffer than Col VII at matched damage. Artifacts: `remote/lammps/*_stress.txt`, `remote/lammps/G_Gpp_summary.json`, `remote/lammps/b3_lammps_run.log`, runner `remote/brev_lammps.sh`.

## Notes

- Brev gateway SSH (`brev exec`/`brev copy`) timed out on both instances ("banner exchange"); worked around with direct-IP SSH port 22 using `~/.brev/brev.pem` (users `shadeform@216.81.248.38` L40S, `ubuntu@89.169.126.119` H100) — same workaround as the B7 A6000 note.
- B2 runs via `docker run --rm --device nvidia.com/gpu=all -v ~/oxt:/work -v oxt-gpu-venv:/tmp/oxt-venv python:3.12.7-bookworm bash remote/gpu_run.sh` (host python3.12 lacks ensurepip, so the bare venv route failed). Outputs will land in `~/oxt/results/gpu/` on the H100; pull back with rsync over the same direct-IP SSH.
- B2 was still running at report time (48x48, 8 seeds, 4680 network systems in 74 batches); it continues after this report.
