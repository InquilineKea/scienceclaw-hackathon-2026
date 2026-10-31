#!/usr/bin/env python3
"""Bounded neutral-fragment relaxation with NVIDIA ALCHEMI Toolkit FIRE2.

This is NOT the NVIDIA BGR NIM HTTP service. No installers or downloads.
Run only after reviewing SECURITY_REVIEW.md and approving this environment.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

SYSTEMS = [
    {"id": "peptide_bond_control", "name": "N-methylacetamide",
     "smiles": "CC(=O)NC", "formula": "C3H7NO",
     "interpretation": "Neutral peptide-bond reference; not collagen."},
    {"id": "capped_glycine", "name": "N-acetylglycine methylamide",
     "smiles": "CC(=O)NCC(=O)NC", "formula": "C5H10N2O2",
     "interpretation": "A capped collagen-related glycine residue; not a triple helix."},
    {"id": "isopeptide_amide_motif", "name": "N-ethylacetamide",
     "smiles": "CC(=O)NCC", "formula": "C4H9NO",
     "interpretation": "Truncated neutral amide motif relevant to an isopeptide link; not a full TG2 crosslink."},
    {"id": "dityrosine_biaryl_core", "name": "2,2'-biphenol",
     "smiles": "Oc1ccccc1-c1ccccc1O", "formula": "C12H10O2",
     "interpretation": "Truncated ortho-linked phenolic biaryl motif; amino-acid side chains removed. Not full dityrosine."},
]
EXPECTED_MODEL_SHA256 = "4842c52ad210d6e1f84d6cf1ffa70fae25a7e0d755ed55cf223f43913f587db7"


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepare(out):
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdMolDescriptors
    manifest, molecules = [], []
    for spec in SYSTEMS:
        base = Chem.MolFromSmiles(spec["smiles"])
        if base is None:
            raise ValueError("Invalid SMILES: " + spec["id"])
        Chem.SanitizeMol(base)
        if len(Chem.GetMolFrags(base)) != 1 or Chem.GetFormalCharge(base) != 0:
            raise ValueError("Pilot requires single connected neutral molecules")
        if any(a.GetNumRadicalElectrons() for a in base.GetAtoms()):
            raise ValueError("Radicals excluded")
        if rdMolDescriptors.CalcMolFormula(base) != spec["formula"]:
            raise ValueError("Unexpected formula")
        for seed in (17, 29):
            mol = Chem.AddHs(base)
            params = AllChem.ETKDGv3()
            params.randomSeed = seed
            if AllChem.EmbedMolecule(mol, params) != 0:
                raise ValueError("Embedding failed")
            if not AllChem.MMFFHasAllMoleculeParams(mol):
                raise ValueError("Incomplete MMFF initialization coverage")
            rc = AllChem.MMFFOptimizeMolecule(mol, mmffVariant="MMFF94s", maxIters=2000)
            if rc != 0:
                raise ValueError("MMFF initialization did not converge")
            sid = spec["id"] + "_seed" + str(seed)
            coords = mol.GetConformer().GetPositions().tolist()
            nums = [a.GetAtomicNum() for a in mol.GetAtoms()]
            bonds = [[b.GetBeginAtomIdx(), b.GetEndAtomIdx(), b.GetBondTypeAsDouble()] for b in mol.GetBonds()]
            rec = dict(spec, structure_id=sid, seed=seed, charge=0, multiplicity=1,
                       canonical_smiles=Chem.MolToSmiles(base), atomic_numbers=nums,
                       initial_coordinates_A=coords, bonds=bonds,
                       mmff_all_parameters=True, mmff_returncode=rc, atom_count=len(nums))
            writer = Chem.SDWriter(str(out / (sid + "_initial.sdf")))
            mol.SetProp("_Name", sid)
            writer.write(mol)
            writer.close()
            manifest.append(rec)
            molecules.append(mol)
    dump(out / "structures.json", manifest)
    # Also retain a NIM-compatible request for a separately reviewed AIMNet2 NIM.
    dump(out / "nim_request.json", {"atoms": [
        {"structure_id": r["structure_id"], "numbers": r["atomic_numbers"],
         "coord": [x for p in r["initial_coordinates_A"] for x in p],
         "charge": 0, "mult": 1} for r in manifest],
        "opttol": 0.02, "cellopt": False,
        "info": "neutral collagen-related fragment pilot; nonperiodic backend required"})
    return manifest, molecules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/out")
    ap.add_argument("--model", default="/models/mace/MACE-OFF23_medium.model")
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--max-steps", type=int, default=1000)
    ap.add_argument("--wall-seconds", type=int, default=480)
    args = ap.parse_args()
    if not 1 <= args.max_steps <= 1000 or not 1 <= args.wall_seconds <= 480:
        raise ValueError("Bounded pilot limits exceeded")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    start = time.time()
    manifest, molecules = prepare(out)
    print("Prepared", len(manifest), "valid neutral conformers", flush=True)
    if args.prepare_only:
        return
    actual_hash = hashlib.sha256(Path(args.model).read_bytes()).hexdigest()
    if actual_hash != EXPECTED_MODEL_SHA256:
        raise ValueError("Unreviewed model checksum")
    import numpy as np
    import torch
    from rdkit import Chem
    from ase import Atoms
    from nvalchemi.data import AtomicData, Batch
    from nvalchemi.dynamics import FIRE2
    from nvalchemi.dynamics.base import ConvergenceHook, DynamicsStage
    from nvalchemi.hooks import NeighborListHook
    from nvalchemi.models.mace import MACEWrapper
    if not torch.cuda.is_available():
        raise RuntimeError("GPU unavailable; CPU fallback forbidden")
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(0.25, 0)
    # Explicit pickle-bearing model load, permitted only inside the approved
    # offline container. This local hash-checked path never invokes download code.
    # Old embedded TorchScript modules can deserialize buffers on CPU even with
    # map_location. Explicitly move the whole module, as upstream's factory does.
    raw = torch.load(args.model, map_location="cuda", weights_only=False)
    raw = raw.to(device="cuda", dtype=torch.float64)
    model = MACEWrapper(raw, train=False)
    model.eval()
    coverage = set(int(z) for z in raw.atomic_numbers.tolist())
    if not set(z for r in manifest for z in r["atomic_numbers"]).issubset(coverage):
        raise ValueError("Model does not cover input elements")
    provenance = {
        "job_label": os.environ.get("PILOT_JOB_LABEL", "unlabelled"),
        "engine": "NVIDIA ALCHEMI Toolkit FIRE2", "nim_service": False,
        "model": "MACE-OFF23 medium", "model_sha256": actual_hash,
        "supported_atomic_numbers": sorted(coverage),
        "gpu": torch.cuda.get_device_name(0), "cuda": torch.version.cuda,
        "versions": {n: importlib.metadata.version(n) for n in
                     ["torch", "nvalchemi-toolkit", "nvalchemi-toolkit-ops", "mace-torch", "rdkit", "ase"]},
        "started_unix": start, "fmax_target_eV_A": 0.02,
        "max_steps": args.max_steps,
        "limits": ["isolated neutral fragments", "no solvent", "no reactions",
                   "no tissue strength inference", "no glucosepane/PYD/4-HNE simulation"],
    }
    dump(out / "provenance.json", provenance)
    data = []
    for r in manifest:
        d = AtomicData.from_atoms(Atoms(numbers=r["atomic_numbers"],
                                       positions=r["initial_coordinates_A"], pbc=False))
        d.positions = d.positions.to(torch.float64)
        d.forces = torch.zeros(d.num_nodes, 3, dtype=torch.float64)
        d.energy = torch.zeros(1, 1, dtype=torch.float64)
        d.add_node_property("velocities", torch.zeros(d.num_nodes, 3, dtype=torch.float64))
        data.append(d)
    batch = Batch.from_data_list(data, device=torch.device("cuda"))
    hook = NeighborListHook(model.model_config.neighbor_config, stage=DynamicsStage.BEFORE_COMPUTE)
    hook._rebuild(batch)
    evaluated = model(batch)
    initial_e = evaluated["energy"].detach().reshape(-1).cpu().tolist()
    ptr = np.cumsum([0] + [r["atom_count"] for r in manifest])
    opt = FIRE2(model=model, dt=0.02, n_steps=args.max_steps,
                convergence_hook=ConvergenceHook(criteria=[
                    {"key": "forces", "threshold": 0.02, "reduce_op": "norm", "reduce_dims": -1}]),
                hooks=[hook])
    trace = (out / "convergence.jsonl").open("w", buffering=1)
    deadline = start + args.wall_seconds
    timed_out = False
    for step in range(args.max_steps):
        if time.time() > deadline:
            timed_out = True
            break
        batch, _ = opt.step(batch)
        if step % 25 == 0:
            forces = batch.forces.detach().norm(dim=1).cpu().numpy()
            fs = [float(forces[ptr[i]:ptr[i+1]].max()) for i in range(len(manifest))]
            row = {"step": opt.step_count, "elapsed_s": time.time()-start, "fmax_eV_A": fs}
            trace.write(json.dumps(row, allow_nan=False) + "\n")
            print(json.dumps(row), flush=True)
            if not all(math.isfinite(f) for f in fs):
                raise ValueError("Nonfinite forces")
            if max(fs) <= 0.02:
                break
    trace.close()
    # Re-evaluate exactly the final coordinates, avoiding stale last-step energy.
    hook._rebuild(batch)
    final = model(batch)
    positions = batch.positions.detach().cpu().numpy()
    energies = final["energy"].detach().reshape(-1).cpu().numpy()
    forces = final["forces"].detach().cpu().numpy()
    if not all(np.isfinite(x).all() for x in (positions, energies, forces)):
        raise ValueError("Nonfinite final output")
    rows = []
    for i, (r, mol) in enumerate(zip(manifest, molecules)):
        p = positions[ptr[i]:ptr[i+1]]
        f = forces[ptr[i]:ptr[i+1]]
        fmax = float(np.linalg.norm(f, axis=1).max())
        p0 = np.array(r["initial_coordinates_A"])
        ratios = [float(np.linalg.norm(p[a]-p[b])/np.linalg.norm(p0[a]-p0[b])) for a,b,_ in r["bonds"]]
        all_dist = np.linalg.norm(p[:, None]-p[None, :], axis=2)
        all_dist[np.diag_indices_from(all_dist)] = np.inf
        geometry_ok = min(ratios) > 0.7 and max(ratios) < 1.3 and float(all_dist.min()) > 0.6
        energy_ok = float(energies[i]) <= initial_e[i] + 0.001
        for j, xyz in enumerate(p):
            mol.GetConformer().SetAtomPosition(j, xyz.tolist())
        writer = Chem.SDWriter(str(out / (r["structure_id"] + "_relaxed.sdf")))
        writer.write(mol)
        writer.close()
        record = {
            "structure_id": r["structure_id"], "compound": r["id"], "atom_count": len(p),
            "initial_energy_eV": initial_e[i], "final_energy_eV": float(energies[i]),
            "energy_change_eV": float(energies[i])-initial_e[i], "fmax_eV_A": fmax,
            "converged": fmax <= 0.02, "geometry_sanity_pass": bool(geometry_ok),
            "energy_nonincrease_pass": bool(energy_ok), "steps": opt.step_count,
            "coordinates_A": p.tolist(), "forces_eV_A": f.tolist(),
            "initial_bond_length_ratio_range": [min(ratios), max(ratios)],
            "minimum_atom_distance_A": float(all_dist.min()),
        }
        record["validation_pass"] = record["converged"] and geometry_ok and energy_ok
        rows.append(record)
    for r in rows:
        same = [x["final_energy_eV"] for x in rows if x["compound"] == r["compound"]]
        r["relative_energy_within_same_compound_eV"] = r["final_energy_eV"] - min(same)
    summary = {"engine": provenance["engine"], "nim_service": False,
               "elapsed_seconds": time.time()-start, "timed_out": timed_out,
               "all_validated": all(r["validation_pass"] for r in rows), "results": rows}
    dump(out / "results.json", summary)
    columns = [k for k,v in rows[0].items() if not isinstance(v, list)]
    with (out / "results.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    dump(out / "explorer_import.json", {
        "schema": "collagen-molecular-evidence-v1", "scope": "local-fragment-geometries",
        "can_update_tissue_stiffness": False, "mechanics_parameters": None,
        "evidence_file": "results.json", "status": "validated" if summary["all_validated"] else "partial",
        "explanation": "Geometry relaxation does not identify tissue strength, rupture force, or reaction rates."})
    print(json.dumps({k:v for k,v in summary.items() if k != "results"}), flush=True)
    if not summary["all_validated"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
