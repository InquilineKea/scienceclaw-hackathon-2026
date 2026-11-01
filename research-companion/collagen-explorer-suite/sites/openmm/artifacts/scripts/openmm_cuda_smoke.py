#!/usr/bin/env python3
"""Strict CUDA harmonic-dimer test. A pass is technical, not biological validation."""
import argparse
import datetime as dt
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "fail",
              "test": "harmonic dimer: CUDA vs Reference, then 1000 NVE steps",
              "biological_validation": False, "fallback_allowed": False}
    try:
        import openmm as mm
        from openmm import unit
        result["openmm_version"] = importlib.metadata.version("openmm")
        result["platforms"] = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
        result["plugin_load_failures"] = list(mm.Platform.getPluginLoadFailures())
        cuda = mm.Platform.getPlatformByName("CUDA")
        system = mm.System()
        for _ in range(2):
            system.addParticle(12 * unit.dalton)
        bond = mm.HarmonicBondForce()
        bond.addBond(0, 1, 0.1, 1000.0)
        system.addForce(bond)
        result["parameters"] = {"particles": 2, "mass_da": 12, "r0_nm": 0.1,
                                "k_kj_mol_nm2": 1000, "initial_r_nm": 0.12,
                                "dt_fs": 1, "steps": 1000, "precision": "mixed"}
        positions = [mm.Vec3(0, 0, 0), mm.Vec3(0.12, 0, 0)] * unit.nanometer
        contexts, integrators, initial = [], [], {}
        for platform in [mm.Platform.getPlatformByName("Reference"), cuda]:
            integrator = mm.VerletIntegrator(1 * unit.femtosecond)
            integrators.append(integrator)
            props = {"Precision": "mixed", "DeviceIndex": "0"} if platform.getName() == "CUDA" else {}
            ctx = mm.Context(system, integrator, platform, props)
            contexts.append(ctx)
            ctx.setPositions(positions)
            ctx.setVelocities([mm.Vec3(0, 0, 0)] * 2)
            state = ctx.getState(getEnergy=True, getForces=True)
            initial[platform.getName()] = {
                "potential_kj_mol": state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole),
                "forces_kj_mol_nm": [[float(x) for x in f] for f in state.getForces().value_in_unit(unit.kilojoule_per_mole / unit.nanometer)],
            }
        result["initial"] = initial
        gpu = contexts[1]
        result["actual_platform"] = gpu.getPlatform().getName()
        result["platform_properties"] = {name: cuda.getPropertyValue(gpu, name) for name in cuda.getPropertyNames()}
        energies = [initial[p]["potential_kj_mol"] for p in ["Reference", "CUDA"]]
        force_error = max(abs(a-b) for fa, fb in zip(initial["Reference"]["forces_kj_mol_nm"], initial["CUDA"]["forces_kj_mol_nm"]) for a, b in zip(fa, fb))
        result["initial_force_max_abs_difference_kj_mol_nm"] = force_error
        if not all(math.isfinite(e) and abs(e - 0.2) < 1e-4 for e in energies):
            raise ValueError("Initial energies disagree with the analytic 0.2 kJ/mol")
        if not math.isfinite(force_error) or force_error > 1e-3:
            raise ValueError("CUDA/Reference force disagreement exceeds 1e-3 kJ/mol/nm")
        integrators[1].step(1000)
        state = gpu.getState(getEnergy=True, getPositions=True)
        total = (state.getPotentialEnergy() + state.getKineticEnergy()).value_in_unit(unit.kilojoule_per_mole)
        coords = [[float(x) for x in p] for p in state.getPositions().value_in_unit(unit.nanometer)]
        drift = abs(total - energies[1]) / energies[1]
        result.update(final_total_kj_mol=total, relative_energy_drift=drift, final_positions_nm=coords)
        if not all(math.isfinite(v) for row in coords for v in row) or not math.isfinite(drift) or drift > 1e-3:
            raise ValueError("NVE finite-value or relative-energy-drift check failed (limit 1e-3)")
        result["status"] = "pass"
    except Exception as exc:
        result.update(error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    result["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
