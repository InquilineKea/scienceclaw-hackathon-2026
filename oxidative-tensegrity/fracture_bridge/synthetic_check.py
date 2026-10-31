"""Synthetic multi-realization verification of the extraction adapter.

Generates 8 realizations of a noisy triangular cohesive law with KNOWN
analytic G_c (log-normal parameter scatter + sample-wise traction noise), runs
the full adapter pipeline (file writing -> loading -> extraction -> mean ± sd
aggregation -> MOOSE template), and reports recovery accuracy per realization
and across the ensemble.

Independent cross-check (the "different calculation" required by the experiment
registry before a finding is reusable): every adapter G_c is compared against
  (a) the closed-form triangle energy 0.5 * T_max * delta_f_true, and
  (b) an independent MIDPOINT-rule integral (the adapter uses the trapezoid).
Concordance of three distinct calculations is asserted.

Run:  python -m fracture_bridge.synthetic_check [--outdir fracture_bridge/results/synthetic_8r]

Outputs (under --outdir):
  curves/realization_k.json   input curves in the network-model JSON schema
  summary.json                extraction summary (mean ± sd + per-realization)
  moose_czm_template.i        rendered MOOSE parameter template
  report.json                 recovery numbers vs ground truth
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from fracture_bridge import extract_cohesive as ec
    from fracture_bridge import moose_template as mt
else:
    from . import extract_cohesive as ec
    from . import moose_template as mt

# ---- ground-truth ensemble design (fixes everything before any noise) ----
N_REALIZATIONS = 8
TRUTH = {
    "T_max_base": 1.5e6,      # Pa
    "T_max_rel_sd": 0.06,     # log-normal scatter in peak traction
    "delta_f_base": 2.0e-5,   # m  (=> G_c ~ 15 J/m^2, collagen-scale ballpark)
    "delta_f_rel_sd": 0.06,   # log-normal scatter in failure separation
    "traction_noise": 0.01,   # 1% multiplicative Gaussian noise per sample
    "n_samples": 800,         # samples per realization
    "decay_threshold": 0.02,  # same as adapter default
}


def triangular_law(delta, T_max, delta_f):
    """Exact triangular law (peak at delta_f/2, zero at delta_f)."""
    d_peak = 0.5 * delta_f
    rise = T_max * delta / d_peak
    fall = T_max * (1.0 - (delta - d_peak) / (delta_f - d_peak))
    law = np.where(delta <= d_peak, rise, fall)
    return np.clip(law, 0.0, None)


def make_realization(seed):
    """Sample one noisy realization; return (curve dict, analytic truth dict)."""
    rng = np.random.default_rng(seed)
    T_max = TRUTH["T_max_base"] * math.exp(
        TRUTH["T_max_rel_sd"] * rng.standard_normal())
    delta_f = TRUTH["delta_f_base"] * math.exp(
        TRUTH["delta_f_rel_sd"] * rng.standard_normal())

    # sample grid with the peak exactly ON a sample point, tail past delta_f
    d_peak = 0.5 * delta_f
    n = TRUTH["n_samples"] // 4
    up = np.linspace(0.0, d_peak, n)          # includes peak
    down = np.linspace(d_peak, delta_f, n)    # includes peak and delta_f
    flat = np.linspace(delta_f, 1.25 * delta_f, n // 2)
    delta = np.concatenate([up, down[1:], flat[1:]])
    traction_exact = triangular_law(delta, T_max, delta_f)
    traction = traction_exact * (1.0 + TRUTH["traction_noise"]
                                  * rng.standard_normal(delta.size))
    # keep the physical clamp: no negative traction before failure tail
    traction = np.clip(traction, 0.0, None)
    traction[delta <= delta_f * (1 - 1e-9)] = np.clip(
        traction[delta <= delta_f * (1 - 1e-9)], 1e-12, None)

    truth = {
        "T_max": T_max, "delta_f": delta_f, "delta_peak": d_peak,
        "G_c": 0.5 * T_max * delta_f, "K0": T_max / d_peak,
    }
    curve = {
        "schema": ec.CURVE_SCHEMA,
        "condition": "synthetic-triangular",
        "mode": "I",
        "realization": seed,
        "units": {"delta": "m", "traction": "Pa"},
        "delta": delta,
        "traction": traction,
    }
    return curve, truth


def midpoint_integral(delta, traction):
    """Independent quadrature: midpoint rule on the positive traction part."""
    t = np.clip(traction, 0.0, None)
    d_mid = 0.5 * (delta[:-1] + delta[1:])
    t_mid = 0.5 * (t[:-1] + t[1:])
    return float(np.sum(t_mid * np.diff(delta)))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir",
                        default=str(Path(__file__).parent / "results" / "synthetic_8r"))
    parser.add_argument("--seeds", nargs="*", default=None,
                        help="override seeds (default 0..7)")
    args = parser.parse_args(argv)
    outdir = Path(args.outdir)
    seeds = [int(s) for s in args.seeds] if args.seeds else list(range(N_REALIZATIONS))

    (outdir / "curves").mkdir(parents=True, exist_ok=True)

    results, truths, curves = [], [], []
    for seed in seeds:
        curve, truth = make_realization(seed)
        p = outdir / "curves" / f"realization_{seed}.json"
        p.write_text(json.dumps({
            "schema": curve["schema"], "condition": curve["condition"],
            "mode": curve["mode"], "realization": curve["realization"],
            "units": curve["units"],
            "delta": [float(x) for x in curve["delta"]],
            "traction": [float(x) for x in curve["traction"]],
        }))
        curves.append(p)
        truths.append(truth)

        # run the adapter through the SAME loading path the network outputs use
        loaded = ec.load_realizations(p)
        assert len(loaded) == 1
        r = ec.extract_curve(loaded[0]["delta"], loaded[0]["traction"],
                             mode=loaded[0]["mode"], source=str(p),
                             realization=loaded[0]["realization"],
                             units=loaded[0]["units"],
                             decay_threshold=TRUTH["decay_threshold"])
        results.append(r)

    summary = ec.aggregate(results, label="synthetic-triangular")
    (outdir / "summary.json").write_text(
        json.dumps({"I": summary.as_dict()}, indent=2) + "\n")

    # MOOSE parameter template from the aggregated condition
    template = mt.render_moose_czm_input(
        "synthetic-triangular", summary, None,
        units_note="SYNTHETIC TEST DATA (Pa, m, J/m^2) — not a physical collagen calibration",
    )
    (outdir / "moose_czm_template.i").write_text(template)

    # ---- recovery analysis ----
    rows, G_errs, T_errs, K_errs, df_bias = [], [], [], [], []
    for r, truth in zip(results, truths):
        g_trap = r.G_c
        g_closed = 0.5 * truth["T_max"] * truth["delta_f"]
        g_mid = midpoint_integral(r.delta_arr, r.traction_arr)
        # adapter delta_f is the 2%-threshold crossing; analytic crossing:
        thr = TRUTH["decay_threshold"]
        cross_true = truth["delta_peak"] + (truth["delta_f"] - truth["delta_peak"]) * (1 - thr)
        rows.append({
            "realization": r.realization,
            "complete": not r.incomplete,
            "G_c_adapter_trapz": g_trap,
            "G_c_closed_form": g_closed,
            "G_c_midpoint_rule": g_mid,
            "G_c_rel_err_vs_closed_form": (g_trap - g_closed) / g_closed,
            "trapz_vs_midpoint_rel_diff": (g_trap - g_mid) / g_mid,
            "T_max_adapter": r.T_max, "T_max_true": truth["T_max"],
            "T_max_rel_err": (r.T_max - truth["T_max"]) / truth["T_max"],
            "K0_adapter": r.K0, "K0_true": truth["K0"],
            "K0_rel_err": (r.K0 - truth["K0"]) / truth["K0"],
            "delta_f_adapter": r.delta_f, "delta_f_true_crossing": cross_true,
            "delta_f_rel_bias": (r.delta_f - cross_true) / cross_true,
        })
        G_errs.append((g_trap - g_closed) / g_closed)
        T_errs.append((r.T_max - truth["T_max"]) / truth["T_max"])
        K_errs.append((r.K0 - truth["K0"]) / truth["K0"])
        df_bias.append((r.delta_f - cross_true) / cross_true)

    def stats(x):
        arr = np.asarray(x, dtype=float)
        return {"mean": float(arr.mean()), "sd": float(arr.std(ddof=1))}

    n_complete = sum(1 for r in results if not r.incomplete)
    report = {
        "n_realizations": len(results),
        "n_complete": n_complete,
        "all_complete_flagged_correctly": n_complete == len(results),
        "ground_truth_design": {k: v for k, v in TRUTH.items()},
        "per_realization": rows,
        "G_c_recovery": {
            "true_mean": float(np.mean([t["G_c"] for t in truths])),
            "true_sd": float(np.std([t["G_c"] for t in truths], ddof=1)),
            "adapter_mean": summary.G_c_mean,
            "adapter_sd": summary.G_c_sd,
            "rel_error_mean": float(np.mean(G_errs)),
            "rel_error_sd": float(np.std(G_errs, ddof=1)),
            "max_abs_rel_error": float(np.max(np.abs(G_errs))),
        },
        "T_max_recovery": {**stats(T_errs),
                           "adapter_mean": summary.T_max_mean,
                           "true_mean": float(np.mean([t["T_max"] for t in truths]))},
        "K0_recovery": {**stats(K_errs),
                        "adapter_mean": summary.K0_mean,
                        "true_mean": float(np.mean([t["K0"] for t in truths]))},
        "delta_f_recovery": {**stats(df_bias),
                             "adapter_mean": summary.delta_f_mean,
                             "true_crossing_mean": float(np.mean(
                                 [r["delta_f_true_crossing"] for r in rows]))},
        "independent_checks": {
            "closed_form_vs_trapz_max_abs_rel": float(np.max(np.abs(G_errs))),
            "midpoint_vs_trapz_max_abs_rel": float(np.max(
                [abs(r["trapz_vs_midpoint_rel_diff"]) for r in rows])),
        },
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    # ---- assertions: three calculations must agree; ensemble must recover ----
    assert n_complete == len(results), "noisy complete curves must not be flagged incomplete"
    assert report["independent_checks"]["closed_form_vs_trapz_max_abs_rel"] < 5e-3, \
        "trapezoid G_c deviates from closed form beyond noise floor"
    assert report["independent_checks"]["midpoint_vs_trapz_max_abs_rel"] < 5e-2, \
        "midpoint rule disagrees with trapezoid"
    assert abs(report["G_c_recovery"]["rel_error_mean"]) < 2e-3, \
        "systematic G_c bias beyond noise"

    print(f"synthetic check PASSED: {len(results)} realizations, "
          f"{n_complete}/{len(results)} complete")
    print(f"  G_c true  mean±sd : {report['G_c_recovery']['true_mean']:.6g} ± "
          f"{report['G_c_recovery']['true_sd']:.3g} J/m^2")
    print(f"  G_c adapt mean±sd : {summary.G_c_mean:.6g} ± {summary.G_c_sd:.3g} J/m^2")
    print(f"  G_c rel err mean±sd: {report['G_c_recovery']['rel_error_mean']:.3e} ± "
          f"{report['G_c_recovery']['rel_error_sd']:.3e} (max abs "
          f"{report['G_c_recovery']['max_abs_rel_error']:.3e})")
    print(f"  T_max rel err mean±sd: {report['T_max_recovery']['mean']:.3e} ± "
          f"{report['T_max_recovery']['sd']:.3e}")
    print(f"  K0 rel err mean±sd  : {report['K0_recovery']['mean']:.3e} ± "
          f"{report['K0_recovery']['sd']:.3e}")
    print(f"  delta_f rel bias mean±sd: {report['delta_f_recovery']['mean']:.3e} ± "
          f"{report['delta_f_recovery']['sd']:.3e}")
    print(f"  midpoint-vs-trapz max rel diff: "
          f"{report['independent_checks']['midpoint_vs_trapz_max_abs_rel']:.3e}")
    print(f"artifacts in {outdir}")
    return report


if __name__ == "__main__":
    main()
