#!/usr/bin/env python3
"""Mechanical completion checks only; passing does not validate the biological model."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("run_dir", type=Path)
p.add_argument("--em-only", action="store_true")
p.add_argument("--mode", choices=["gpu", "cpu"], default="gpu")
a = p.parse_args()
r = a.run_dir
log = (r / "em.log").read_text(errors="replace")
f = re.search(r"Maximum force\s*=\s*([0-9.Ee+-]+)", log)
assert f and math.isfinite(float(f[1])) and float(f[1]) < 1000, "EM maximum force not <1000 kJ/mol/nm"
if a.em_only:
    print("EM maximum force criterion passed; continue short equilibration")
    raise SystemExit(0)
for stage in ("nvt", "npt", "sample"):
    for extension in ("log", "gro", "edr", "tpr", "cpt", "xtc"):
        assert (r / f"{stage}.{extension}").stat().st_size > 0
    text = (r / f"{stage}.log").read_text(errors="replace")
    assert "Finished mdrun" in text, f"{stage}: completion marker missing"
    assert not re.search(r"LINCS WARNING|Fatal error|constraint failure", text, re.I), f"{stage}: numerical failure"
    if a.mode == "gpu":
        # Unlike wrapper gpu_selected, this requires the actual engine assignment statement.
        assert re.search(r"[Ss]hort[- ]range.*GPU|[Gg]PU.*short[- ]range", text), f"{stage}: inspect GPU assignment manually"
def xvg(path):
    rows = [[float(x) for x in line.split()] for line in path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith(("#", "@"))]
    assert rows and all(all(math.isfinite(x) for x in row) for row in rows), f"Invalid data in {path}"
    return rows
energy = xvg(r / "sample-energy.xvg")
rmsd = xvg(r / "backbone-rmsd.xvg")
assert len(energy) >= 21 and energy[-1][0] >= 20.0 - 1e-4, "Sample stopped before 20 ps"
assert len(rmsd) >= 21 and rmsd[-1][0] >= 20.0 - 1e-4
hashes = {str(f.relative_to(r)): hashlib.sha256(f.read_bytes()).hexdigest()
          for f in sorted(r.rglob("*")) if f.is_file() and f.name != "verification.json"}
result = {"status": "SHORT_BASELINE_COMPLETED_NOT_SCIENTIFICALLY_VALIDATED", "maximum_force": float(f[1]),
          "requested_device": a.mode, "sample_end_time_ps": energy[-1][0],
          "energy_frames": len(energy), "rmsd_frames": len(rmsd),
          "manual_review_required": ["Topology net charge and chain termini", "Temperature/density relaxation",
                                     "Imaging of triple helix before interpreting RMSD", "Longer independent replicas",
                                     "Force-field accuracy for scientific question"], "sha256": hashes}
(r / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k:v for k,v in result.items() if k != "sha256"}, indent=2))
