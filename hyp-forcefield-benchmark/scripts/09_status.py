"""Step 8: ledger of completed vs proposed calculations -> STATUS.md and results/status.json"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench.ffreg import FORCEFIELDS, ROOT  # noqa: E402

R = os.path.join(ROOT, "results")
q = json.load(open(os.path.join(R, "qm_vs_mm.json")))
m = json.load(open(os.path.join(R, "md_summary.json")))
g = json.load(open(os.path.join(R, "qm_geometries.json")))
planned = json.load(open(os.path.join(R, "dft_planned_jobs.json")))
done_keys = set()
for line in open(os.path.join(R, "dft_energies.jsonl")):
    r = json.loads(line)
    done_keys.add((r["index"], r["method"]))
by = {}
for j in planned:
    k = (j["method"], j["scan"].split("_")[0] if j["scan"].startswith(("phi", "psi", "ohrot")) and False else j["scan"])
    by.setdefault(k, [0, 0])
    by[k][1] += 1
    by[k][0] += (j["index"], j["method"]) in done_keys
lines = ["# Status ledger (generated)", "", "## Completed", "",
         f"- GFN2-xTB constrained geometries: {len(g['points'])} of {len(g['points'])} points",
         f"- Gas-phase MM re-optimisations on the QM grid: {len(g['points'])} points x {len(FORCEFIELDS)} force fields"]
status = dict(dft=[], md=[], proposed=[])
for (method, scan), (d, n) in sorted(by.items()):
    status["dft"].append(dict(method=method, scan=scan, done=d, planned=n))
    if d:
        lines.append(f"- DFT {method}, {scan}: {d} of {n} single points")
for key, rec in m["runs"].items():
    hy = rec["residues"].get("HYP", {})
    status["md"].append(dict(run=key, ps=rec["ps"], water=rec["water"], hyp_transitions=hy.get("n_transitions")))
    lines.append(f"- MD {key} ({rec['water']}): {rec['ps']:.0f} ps production, {hy.get('n_transitions')} Hyp pucker transitions")
lines += ["", "## Not completed (proposed)", ""]
for (method, scan), (d, n) in sorted(by.items()):
    if d < n:
        lines.append(f"- DFT {method}, {scan}: {n - d} of {n} single points not run")
        status["proposed"].append(f"DFT {method} {scan}: {n - d} points")
for key in m["not_run"]:
    lines.append(f"- MD {key}: not run")
    status["proposed"].append(f"MD {key}")
lines += [
    "- Production-length MD (>= 200 ns dipeptide, >= 500 ns triple helix per force field, >= 3 replicas): not run",
    "- (Pro-Hyp-Gly)10 triple helix (the experimentally characterised peptide): not run; a (Pro-Hyp-Gly)3 segment was used",
    "- DFT geometry optimisation of the conformers at the DFT level (instead of GFN2-xTB geometries): not run",
    "- Wavefunction reference (DLPNO-CCSD(T) or MP2/CBS) for the six conformers: not run",
    "- Comparison of the reconstructed CHARMM36mGP with the authors' files (Zenodo 10.5281/zenodo.15354101): not possible here",
    "- NMR observables (3J couplings, 15N relaxation) and SAXS back-calculation: not run", ""]
status["proposed"] += ["production MD", "(POG)10", "DFT-level geometries", "wavefunction reference", "C36mGP file comparison", "NMR/SAXS observables"]
open(os.path.join(ROOT, "STATUS.md"), "w").write("\n".join(lines))
json.dump(status, open(os.path.join(R, "status.json"), "w"), indent=1)
print("\n".join(lines))
