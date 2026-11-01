#!/usr/bin/env python3
"""Back-of-envelope power / cost estimate for the four-arm ColBuilder loading study (Codex, L40S).

Every input below is an ASSUMPTION unless marked measured. Throughput is not measured yet.
Measured inputs come from Codex's outputs:
  grip separation L0 = 65.013 nm (thermal-loading-preview-r4), 34,754 CA = 11.02 molecule-equivalents,
  41-60 triple-helix segments crossing each axial plane (counted from the native-control PDB CA z),
  box 18.82 x 19.81 nm, all 10 GLU bridges inside z = 46.21-46.46 nm (one site pair, AGS523/LGX286).
"""
import json
import math

KT = 2.494            # kJ/mol at 300 K
NM2_PER_NPM = 602.214  # 1 N/m = 602.2 kJ/mol/nm^2
L0 = 65.013           # nm, measured grip separation
SEG_MIN, SEG_MED = 40.7, 48.5     # measured helix segments crossing a plane (min = gap-like plane)
BOX_AREA = 18.8171 * 19.80747     # nm^2, water box (NOT the specimen area)


def k_spec(E_gpa, area_nm2):
    return E_gpa * 1e9 * area_nm2 * 1e-18 / (L0 * 1e-9) * NM2_PER_NPM  # kJ/mol/nm^2


def main():
    out = {"assumptions": {
        "E_GPa": [0.3, 1.0, 2.0], "area_per_helix_nm2": [1.3, 2.0],
        "density_g_cm3": 1.2, "tau_int_ps_global": [20, 100], "strain_window": 0.01,
        "l40s_ns_per_day_1fs": [3, 6], "usd_per_h": {"L40S": 2.14, "H100": 5.4},
        "local_sigma_nm": [0.05, 0.10], "local_tau_ps": [5, 10]}}

    # 1. Specimen stiffness, acoustic transit and per-sample precision of the global slope
    rows = []
    for E in (0.3, 1.0, 2.0):
        for a_h in (1.3, 2.0):
            A = SEG_MIN * a_h
            k = k_spec(E, A)
            c = math.sqrt(E * 1e9 / 1200.0)                 # m/s
            transit_ps = L0 * 1e-9 / c * 1e12
            r0 = math.sqrt(KT / k) / (0.01 * L0)            # rel. SE of slope per independent sample
            n_eff = {m: 2 * (2.8 * r0 / m) ** 2 for m in (0.01, 0.03, 0.085)}
            rows.append({"E_GPa": E, "A_protein_nm2": round(A, 1), "A_over_box": round(A / BOX_AREA, 3),
                         "k_spec_kJmol_nm2": round(k, 1), "acoustic_transit_ps": round(transit_ps, 1),
                         "rel_slope_SE_per_independent_sample": round(r0, 4),
                         "n_eff_per_arm_for_MDE": {f"{100*m:g}%": round(v) for m, v in n_eff.items()},
                         "ns_per_arm_for_MDE_tau20_100": {f"{100*m:g}%": [round(v * 2 * t / 1000, 1) for t in (20, 100)]
                                                          for m, v in n_eff.items()}})
    out["global_slope"] = rows

    # 2. Codex's commissioning cycle: 5-ps ramps, 5-ps holds, 40 ps total
    out["commissioning_cycle_check"] = {
        "ramp_ps": 5, "hold_ps": 5, "strain_rate_per_s": 1e9,
        "grip_speed_m_per_s": round(0.005 * L0 * 1e-9 / 5e-12, 1),
        "note": "ramp is 5-30x shorter than the axial acoustic transit across L0 for E=0.3-2 GPa, so dF/dq "
                "in that cycle is an inertial/viscous transient, not an elastic slope"}

    # 3. Local readout: relative axial sliding of the two attachment segments at each bridge site
    loc = []
    for sig in (0.05, 0.10):
        for tau in (5, 10):
            for hold in (40, 200, 500):
                n = hold / (2 * tau)
                se_site = sig * math.sqrt(2 / n)          # difference of two hold means
                se_arm = se_site / math.sqrt(5 * 3)        # 5 sites x 3 replicas
                loc.append({"sigma_nm": sig, "tau_ps": tau, "hold_ps": hold,
                            "SE_per_site_nm": round(se_site, 4),
                            "MDE_arm_contrast_nm_5sites_3reps": round(2.8 * se_arm * math.sqrt(2), 4)})
    out["local_sliding"] = loc

    # 4. Cost of a revised, quasi-static-enough schedule per arm per replica
    sched_ps = {"restrained_nvt": 10, "release": 90, "ramp_0_1pct": 300, "hold_1pct": 300,
                "ramp_1_2pct": 300, "hold_2pct": 300, "no_pull_drift": 600}
    ns = sum(sched_ps.values()) / 1000
    runs = 4 * 3
    cost = {}
    for nsd in (3, 6):
        h_run = ns / nsd * 24
        cost[f"{nsd}ns_day"] = {"h_per_run": round(h_run, 1), "gpu_h_total_12_runs": round(h_run * runs, 1),
                                "usd_L40S": round(h_run * runs * 2.14), "usd_H100_if_1.7x": round(h_run * runs / 1.7 * 5.4),
                                "wall_h_on_4_GPUs_parallel": round(h_run * runs / 4, 1)}
    out["revised_schedule"] = {"ps": sched_ps, "ns_per_run": ns, "runs": "4 arms x 3 replicas", "cost": cost}
    print(json.dumps(out, indent=1))
    with open("results/atomistic_power_plan.json", "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
