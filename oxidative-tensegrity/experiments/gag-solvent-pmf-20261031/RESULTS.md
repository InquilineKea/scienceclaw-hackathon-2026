# Collagen–GAG binding in explicit water: Arg / Lys / charge-lost analogs vs methyl sulfate

Run 2026-10-31/11-01 on Nebius H100 `collagen-pilot-h100-20261031`, OpenMM 8.6.1 (Codex-approved hash-pinned wheels,
digest-pinned Python image, `--network none`, read-only root, all capabilities dropped). CHARMM36 model compounds
shipped in the wheel, TIP3P, 0.15 M NaCl, 300 K, 1 bar. 60/60 simulations finished; all output hashes match the H100.

| analog (stands for) | contact minimum | well depth | ΔG° umbrella+WHAM | ΔG° unbiased MD (independent) |
|---|---|---|---|---|
| methylguanidinium (Arg) | 0.45–0.50 nm | −1.6 kT | −0.50 ± 0.03 kcal/mol | −0.63 ± 0.10 (6 × 3 ns) |
| methylammonium (Lys) | 0.40 nm | −1.3 kT | −0.24 ± 0.09 | −0.14 ± 0.12 (6 × 3 ns) |
| dimethylamine (charge lost) | none | ≈ −0.2 kT | +0.16 ± 0.04 | not run |

ΔG° uses the automatic contact cutoff (~0.78 nm). It is cutoff-sensitive: at 0.55 nm the three values are
+0.05 / +0.34 / +0.74, at 0.65 nm −0.20 / −0.01 / +0.36 kcal/mol. **The ordering Arg > Lys > charge-lost holds at every
cutoff; absolute values are within ~1 kT of zero.**

**What this says about B5 (vacuum AIMNet2, ~−2.4 eV contact energies):** water and salt shrink ion-pair binding to sulfate
by roughly two orders of magnitude, to kT scale. The B5 *ordering* (Arg binds better than Lys; removing the charge, as
MG-H1/CML-type glycation does, removes binding) survives; its *magnitudes* do not. Any "glycation detaches GAGs" claim
should be stated as a shift of a weak, reversible, many-contact equilibrium, not loss of a strong bond.

Limits: side-chain analogs, not peptides or GAG chains; methyl sulfate stands in for one sulfated GalNAc; dimethylamine
is a crude stand-in for MG-H1/CML charge loss (no MG-H1 ring); no multivalency or chain context; TIP3P/CHARMM36 fixed
charges (no polarisation). Run history: run 1 (14 Arg windows at 1.5 ns) was re-queued with 0.75 ns windows to fit the
approved time; a kernel-cache race killed run 2 (40 tasks failed fast, fixed by per-process caches); an idle-check stop
interrupted run 3 and the user approved restarting it. Logs: `results/container-run*.log`.
