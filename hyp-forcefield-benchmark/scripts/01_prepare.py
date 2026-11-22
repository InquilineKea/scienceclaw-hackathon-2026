"""Step 1: generate derived force-field files, build structures, write provenance."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hypbench import build, ffreg  # noqa: E402

R = os.path.join(ffreg.ROOT, "results")
S = os.path.join(ffreg.ROOT, "structures")
os.makedirs(R, exist_ok=True)
os.makedirs(S, exist_ok=True)

ffreg.make_ff99sb_hyp_xml()
ffreg.make_c36m_hyp_xml()
_, cmap_log = ffreg.make_c36mgp_xml()
json.dump(cmap_log, open(os.path.join(R, "c36mgp_cmap_scaling_log.json"), "w"), indent=1)

# Ace-Hyp-NMe cut from chain A (Hyp20: Y position, 5 residues from the Gly->Ala site, 10 from the C-terminus)
top, pos = build.build_capped([("A", 20, 20)])
build.write_pdb(os.path.join(S, "ace_hyp_nme.pdb"), top, pos)
# (Pro-Hyp-Gly)3 x 3 triple helix, residues 19-27 of each chain (downstream of the Ala15 substitution)
top3, pos3 = build.build_capped([("A", 19, 27), ("B", 49, 57), ("C", 79, 87)])
build.write_pdb(os.path.join(S, "pog3_triple_helix.pdb"), top3, pos3)

prov = ffreg.provenance()
prov["_structures"] = {
    "source": "PDB 1CAG (two GitHub mirrors, coordinate records identical)",
    "sha256": ffreg.sha256(build.PDB_1CAG),
    "ace_hyp_nme": "chain A Hyp20 + caps from Pro19/Gly21 backbone atoms",
    "pog3_triple_helix": "chains A 19-27, B 49-57, C 79-87 (same sequence register) + caps",
}
json.dump(prov, open(os.path.join(R, "provenance.json"), "w"), indent=1)
print("atoms dipeptide", top.getNumAtoms(), "triple helix", top3.getNumAtoms())
print("CMAP entries rescaled for C36mGP:", len(cmap_log))
for name in ffreg.FORCEFIELDS:
    fam = ffreg.FORCEFIELDS[name]["family"]
    ff = ffreg.load(name, water=None)
    for label, t in (("dipeptide", top), ("helix", top3)):
        tt = build.topology_for(fam, t)
        sysm = ff.createSystem(tt)
        tm = ff.getMatchingTemplates(tt) if fam == 'amber' else []  # CHARMM caps are patches (resolved inside createSystem)
        q = sum(f.getParticleParameters(i)[0]._value for f in sysm.getForces() if f.__class__.__name__ == "NonbondedForce"
                for i in range(sysm.getNumParticles()))
        print(f"{name:8s} {label:9s} ok  net charge {q:+.4f}  templates: {sorted(set(x.name for x in tm))}")
