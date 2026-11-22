"""Step 5: explicit-solvent MD.  usage: 05_md.py SYSTEM NS FF [FF ...]   (resumable)"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import ffreg, md  # noqa: E402

system, ns, ffs = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
for ff in ffs:
    md.run(ff, system, ns, os.path.join(ffreg.ROOT, "md", f"{system}_{ff}"), threads=int(os.environ.get("MD_THREADS", "1")))
print("MD DONE", system, ffs, flush=True)
