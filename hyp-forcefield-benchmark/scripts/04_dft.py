"""Step 3b: DFT single points on the xTB geometries.  Resumable: appends to results/dft_energies.jsonl.

Priority order (so that an interrupted run still leaves a usable core set):
  1. B3LYP-D3(BJ)/def2-SVP : minima + chi2 pucker scan
  2. sensitivity at exo-min / endo-min / chi2=0 : def2-TZVP basis; PBE0-D3(BJ) and M06-2X functionals
  3. B3LYP-D3(BJ)/def2-SVP : psi scans, phi scans, OH rotamers
usage: python 04_dft.py [threads]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import qm  # noqa: E402
from hypbench.ffreg import ROOT  # noqa: E402

threads = int(sys.argv[1]) if len(sys.argv) > 1 else 1
max_jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 10**6
G = json.load(open(os.path.join(ROOT, "results", "qm_geometries.json")))
OUT = os.path.join(ROOT, "results", "dft_energies.jsonl")
METHODS = {
    "B3LYP-D3BJ/def2-SVP": dict(xc="b3lyp", basis="def2-svp", disp="d3bj"),
    "B3LYP-D3BJ/def2-TZVP": dict(xc="b3lyp", basis="def2-tzvp", disp="d3bj"),
    "PBE0-D3BJ/def2-SVP": dict(xc="pbe0", basis="def2-svp", disp="d3bj"),
    "M06-2X/def2-SVP": dict(xc="m062x", basis="def2-svp", disp=None, grid=4),
    "B3LYP-D3BJ/def2-SVP/ddCOSMO(water)": dict(xc="b3lyp", basis="def2-svp", disp="d3bj", solvent_eps=78.3553),
}
pts = G["points"]
idx = {(p["scan"], p["label"]): i for i, p in enumerate(pts)}
key3 = [idx[("minimum", "exo")], idx[("minimum", "endo")], idx[("pucker", "+0.0")]]
SVP = "B3LYP-D3BJ/def2-SVP"
COARSE = ("+180", "-120", "-60", "+0", "+60", "+120")
jobs = [(i, SVP) for i, p in enumerate(pts) if p["scan"] in ("minimum", "pucker")]
jobs += [(i, "B3LYP-D3BJ/def2-TZVP") for i in key3]
jobs += [(i, SVP) for i, p in enumerate(pts) if p["scan"].startswith("ohrot_")]
jobs += [(i, SVP) for i, p in enumerate(pts) if p["scan"] == "psi_exo" and p["label"] in COARSE]
jobs += [(i, "B3LYP-D3BJ/def2-SVP/ddCOSMO(water)") for i, p in enumerate(pts) if p["scan"] == "minimum" or p["scan"].startswith("ohrot_")]
jobs += [(i, "PBE0-D3BJ/def2-SVP") for i in key3]
jobs += [(i, SVP) for i, p in enumerate(pts) if p["scan"] == "psi_exo" and p["label"] not in COARSE]
jobs += [(i, "M06-2X/def2-SVP") for i in key3]
jobs += [(i, SVP) for i, p in enumerate(pts) if p["scan"] == "psi_endo"]
jobs += [(i, SVP) for i, p in enumerate(pts) if p["scan"].startswith("phi_")]
json.dump([dict(index=i, scan=pts[i]["scan"], label=pts[i]["label"], method=m) for i, m in jobs],
          open(os.path.join(ROOT, "results", "dft_planned_jobs.json"), "w"))

done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        r = json.loads(line)
        done.add((r["index"], r["method"]))
for i, m in jobs[:max_jobs]:
    if (i, m) in done:
        continue
    t = time.time()
    r = qm.dft_sp(G["symbols"], pts[i]["xyz"], threads=threads, **METHODS[m])
    r.update(index=i, scan=pts[i]["scan"], label=pts[i]["label"], method=m, seconds=round(time.time() - t, 1))
    with open(OUT, "a") as f:
        f.write(json.dumps(r) + "\n")
    print(r["scan"], r["label"], m, r["e_tot"], r["converged"], r["seconds"], flush=True)
print("DFT QUEUE FINISHED up to job", min(max_jobs, len(jobs)), "of", len(jobs), flush=True)
