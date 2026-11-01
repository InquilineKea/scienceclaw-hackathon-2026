"""Extraction adapter: network-scale traction-separation curves -> cohesive-zone parameters.

Pipeline position:  fiber-network model (notched oxt networks, irreversible failure)
                    -> T(delta) curves (JSON/CSV, per condition x realization x mode)
                    -> THIS ADAPTER -> {G_c, T_max, delta_peak, delta_f, K0, completeness}
                    -> fracture_bridge.moose_template -> MOOSE CZM input parameters.

Repo rules honoured: stdlib + numpy only; nothing here runs MOOSE or touches oxt/.

Input schema (JSON), one realization per file::

    {
      "schema": "oxt-fracture-bridge/curve@1",
      "condition": "healthy-z3.5-age0",     # free-form condition label
      "mode": "I",                          # "I" (normal) or "II" (shear); default "I"
      "realization": 3,                    # seed / realization id
      "units": {"delta": "m", "traction": "Pa"},   # informational; see README calibration section
      "delta":   [0.0, 1e-6, ...],         # crack opening / separation, ascending
      "traction":[0.0, 5.1e4, ...]         # traction T(delta), same length
    }

or a bundle of realizations in one file::

    {"schema": "oxt-fracture-bridge/bundle@1",
     "condition": "...", "realizations": [ <curve>, <curve>, ... ]}

CSV schemas (with header row): single realization ``delta,traction`` (optional
``mode`` column), or long format ``realization,mode,delta,traction`` which is
grouped into realizations automatically.

Definitions used by the adapter
-------------------------------
G_c      trapezoid integral of the *positive part* of T(delta) over delta:
         G_c = ∫ max(T,0) dδ   [force/length in 2D network units, J/m^2 once
         physically calibrated — see README.md].
T_max    peak traction on the curve.
delta_peak  separation at first occurrence of T_max.
delta_f  separation where the decaying branch first crosses
         ``decay_threshold * T_max`` (linear interpolation between samples).
         None if the curve never decays below the threshold.
incomplete  True when T(delta_max) > decay_threshold * T_max (traction has not
         failed at the largest recorded separation) — G_c is then reported as a
         lower bound and must not be used for production MOOSE parameters.
K0       secant stiffness to peak, K0 = T_max / delta_peak (for a triangular
         law this equals the constant initial stiffness).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# numpy 2 renamed trapz -> trapezoid; support both (runtime-safe on either).
try:
    _trapezoid = np.trapezoid  # numpy >= 2
except AttributeError:
    _trapezoid = getattr(np, "trapz")  # numpy < 2 (removed from numpy 2 stubs)

DEFAULT_DECAY_THRESHOLD = 0.02  # fraction of T_max; below this the cohesive bond is "failed"
DEFAULT_MIN_CURVE_POINTS = 3

CURVE_SCHEMA = "oxt-fracture-bridge/curve@1"
BUNDLE_SCHEMA = "oxt-fracture-bridge/bundle@1"


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def _coerce_arrays(delta, traction, source):
    delta = np.asarray(delta, dtype=float)
    traction = np.asarray(traction, dtype=float)
    if delta.ndim != 1 or traction.ndim != 1:
        raise ValueError(f"[{source}] delta/traction must be 1-D arrays")
    if delta.size != traction.size:
        raise ValueError(
            f"[{source}] length mismatch: {delta.size} delta vs {traction.size} traction"
        )
    if delta.size == 0:
        raise ValueError(f"[{source}] empty curve")
    if not (np.all(np.isfinite(delta)) and np.all(np.isfinite(traction))):
        raise ValueError(f"[{source}] non-finite values in curve")
    order = np.argsort(delta, kind="stable")
    delta, traction = delta[order], traction[order]
    if np.any(np.diff(delta) <= 0):
        raise ValueError(f"[{source}] delta must be strictly increasing after sort")
    return delta, traction


def _curve_from_payload(payload, source):
    if not isinstance(payload, dict) or "delta" not in payload or "traction" not in payload:
        raise ValueError(f"[{source}] payload lacks 'delta'/'traction' arrays")
    mode = str(payload.get("mode", "I")).strip().upper()
    if mode not in ("I", "II"):
        raise ValueError(f"[{source}] mode must be 'I' or 'II', got {mode!r}")
    delta, traction = _coerce_arrays(
        payload["delta"], payload["traction"], source
    )
    return {
        "condition": payload.get("condition"),
        "mode": mode,
        "realization": payload.get("realization", 0),
        "units": payload.get("units", {}),
        "delta": delta,
        "traction": traction,
        "source": source,
    }


def load_realizations(path):
    """Load one or many curve realizations from a JSON or CSV file.

    Returns a list of dict curves (keys: condition, mode, realization, units,
    delta (np.ndarray), traction (np.ndarray), source).
    """
    path = Path(path)
    if path.suffix.lower() == ".json":
        with open(path) as fh:
            payload = json.load(fh)
        if isinstance(payload, dict) and "realizations" in payload:
            base = {
                "condition": payload.get("condition"),
                "units": payload.get("units", {}),
            }
            out = []
            for entry in payload["realizations"]:
                merged = dict(base)
                merged.update(entry)
                out.append(_curve_from_payload(merged, str(path)))
            return out
        return [_curve_from_payload(payload, str(path))]

    # CSV
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"[{path}] CSV has no header row")
        cols = {c.strip().lower() for c in reader.fieldnames}
        if not {"delta", "traction"}.issubset(cols):
            raise ValueError(f"[{path}] CSV needs 'delta' and 'traction' columns")
        rows = [{(k.strip().lower() if k else k): v for k, v in r.items()} for r in reader]

    if "realization" in cols:
        groups = {}
        meta = {}
        for row in rows:
            key = (row.get("realization") or "0", row.get("mode") or "I")
            groups.setdefault(key, []).append(row)
            meta.setdefault(key, row)
        out = []
        for key, group in groups.items():
            real, mode = key
            delta, traction = _coerce_arrays(
                [float(r["delta"]) for r in group],
                [float(r["traction"]) for r in group],
                f"{path}[real={real},mode={mode}]",
            )
            out.append(
                {
                    "condition": meta[key].get("condition"),
                    "mode": str(mode).strip().upper(),
                    "realization": real,
                    "units": {},
                    "delta": delta,
                    "traction": traction,
                    "source": str(path),
                }
            )
        return out

    if len(rows) == 0:
        raise ValueError(f"[{path}] CSV has no data rows")
    mode = str(rows[0].get("mode", "I")).strip().upper()
    delta, traction = _coerce_arrays(
        [float(r["delta"]) for r in rows],
        [float(r["traction"]) for r in rows],
        str(path),
    )
    return [
        {
            "condition": rows[0].get("condition"),
            "mode": mode,
            "realization": rows[0].get("realization", 0),
            "units": {},
            "delta": delta,
            "traction": traction,
            "source": str(path),
        }
    ]


# --------------------------------------------------------------------------- #
# single-curve extraction
# --------------------------------------------------------------------------- #
@dataclass
class CurveResult:
    """Reduced cohesive-zone parameters for ONE T(delta) realization."""

    source: str
    mode: str
    realization: object
    n_points: int
    G_c: float                    # ∫ max(T,0) dδ over the recorded range
    T_max: float
    delta_peak: float
    delta_f: float | None          # None if incomplete
    K0: float                      # T_max / delta_peak
    incomplete: bool
    reason: str                    # "" when complete; else why it is incomplete
    G_c_lower_bound: bool          # True iff incomplete (energy is truncated)
    delta_end: float
    T_end: float
    decay_threshold: float
    units: dict = field(default_factory=dict)
    # raw arrays (kept for table rendering; deliberately not serialized)
    delta_arr: object = field(default=None, repr=False, compare=False)
    traction_arr: object = field(default=None, repr=False, compare=False)

    def as_dict(self):
        return {
            "source": self.source,
            "mode": self.mode,
            "realization": self.realization,
            "n_points": self.n_points,
            "G_c": self.G_c,
            "T_max": self.T_max,
            "delta_peak": self.delta_peak,
            "delta_f": self.delta_f,
            "K0": self.K0,
            "incomplete": self.incomplete,
            "reason": self.reason,
            "G_c_lower_bound": self.G_c_lower_bound,
            "delta_end": self.delta_end,
            "T_end": self.T_end,
            "decay_threshold": self.decay_threshold,
            "units": dict(self.units),
        }


def extract_curve(
    delta,
    traction,
    mode="I",
    source="",
    realization=0,
    units=None,
    decay_threshold=DEFAULT_DECAY_THRESHOLD,
    min_points=DEFAULT_MIN_CURVE_POINTS,
):
    """Reduce one traction-separation curve to cohesive-zone parameters.

    Raises ValueError on malformed input. ``decay_threshold`` is the fraction
    of T_max below which the decaying branch counts as fully failed.
    """
    delta, traction = _coerce_arrays(delta, traction, source or "curve")
    if delta.size < min_points:
        raise ValueError(f"[{source}] needs >= {min_points} points, got {delta.size}")
    if not (0.0 < decay_threshold < 1.0):
        raise ValueError("decay_threshold must be in (0, 1)")
    if traction.max() <= 0.0:
        raise ValueError(f"[{source}] no positive traction; curve cannot represent cohesive failure")

    thr = decay_threshold * traction.max()
    peak_idx = int(np.argmax(traction))
    T_max = float(traction[peak_idx])
    delta_peak = float(delta[peak_idx])
    K0 = T_max / delta_peak if delta_peak > 0 else float("inf")

    # failure separation: first crossing of the decay threshold AFTER the peak
    delta_f = None
    reason = ""
    for i in range(peak_idx + 1, delta.size):
        if traction[i] <= thr:
            if traction[i] == traction[i - 1]:
                delta_f = float(delta[i])
            else:
                t1, t2 = float(traction[i - 1]), float(traction[i])
                d1, d2 = float(delta[i - 1]), float(delta[i])
                delta_f = d1 + (t1 - thr) * (d2 - d1) / (t1 - t2)
            break

    incomplete = delta_f is None
    if incomplete:
        T_end = float(traction[-1])
        if peak_idx == delta.size - 1:
            reason = (
                f"curve ends at the peak (delta_max={delta[-1]:g} is delta_peak); "
                "no post-peak decay recorded"
            )
        else:
            reason = (
                f"traction at max delta T_end={T_end:.6g} exceeds decay threshold "
                f"{decay_threshold:g} x T_max = {thr:.6g}; energy integral truncated"
            )

    G_c = float(_trapezoid(np.clip(traction, 0.0, None), delta))
    return CurveResult(
        source=source,
        mode=str(mode).upper(),
        realization=realization,
        n_points=int(delta.size),
        G_c=G_c,
        T_max=T_max,
        delta_peak=delta_peak,
        delta_f=delta_f,
        K0=K0,
        incomplete=incomplete,
        reason=reason,
        G_c_lower_bound=incomplete,
        delta_end=float(delta[-1]),
        T_end=float(traction[-1]),
        decay_threshold=float(decay_threshold),
        units=dict(units or {}),
        delta_arr=delta,
        traction_arr=traction,
    )


# --------------------------------------------------------------------------- #
# uncertainty aggregation across realizations
# --------------------------------------------------------------------------- #
def _mean_sd(values):
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return None, None
    mean = sum(vals) / n
    if n == 1:
        return mean, 0.0
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)  # sample sd, ddof=1
    return mean, math.sqrt(var)


@dataclass
class ConditionSummary:
    """mean ± sd of cohesive-zone parameters across realizations of one condition+mode."""

    label: str
    mode: str
    n_realizations: int
    n_complete: int
    n_incomplete: int
    G_c_mean: float
    G_c_sd: float
    T_max_mean: float
    T_max_sd: float
    delta_peak_mean: float
    delta_peak_sd: float
    K0_mean: float
    K0_sd: float
    delta_f_mean: float | None     # over complete realizations only
    delta_f_sd: float | None       # 0.0 if fewer than 2 complete curves
    all_complete: bool
    incomplete_sources: list
    per_realization: list                # list of CurveResult.as_dict()
    delta_f_note: str

    def as_dict(self):
        return {
            "label": self.label,
            "mode": self.mode,
            "n_realizations": self.n_realizations,
            "n_complete": self.n_complete,
            "n_incomplete": self.n_incomplete,
            "all_complete": self.all_complete,
            "G_c": {"mean": self.G_c_mean, "sd": self.G_c_sd},
            "T_max": {"mean": self.T_max_mean, "sd": self.T_max_sd},
            "delta_peak": {"mean": self.delta_peak_mean, "sd": self.delta_peak_sd},
            "K0": {"mean": self.K0_mean, "sd": self.K0_sd},
            "delta_f": {"mean": self.delta_f_mean, "sd": self.delta_f_sd},
            "delta_f_note": self.delta_f_note,
            "incomplete_sources": list(self.incomplete_sources),
            "per_realization": list(self.per_realization),
        }


def aggregate(results, label="condition"):
    """Aggregate a list of CurveResult (single mode) into mean ± sd."""
    if not results:
        raise ValueError("no curve results to aggregate")
    modes = {r.mode for r in results}
    if len(modes) != 1:
        raise ValueError(f"aggregate() expects a single mode, got {sorted(modes)}")
    mode = modes.pop()

    complete = [r for r in results if not r.incomplete]
    incomplete = [r for r in results if r.incomplete]

    G_c_mean, G_c_sd = _mean_sd([r.G_c for r in results])
    T_mean, T_sd = _mean_sd([r.T_max for r in results])
    dp_mean, dp_sd = _mean_sd([r.delta_peak for r in results])
    k_mean, k_sd = _mean_sd([r.K0 for r in results])

    if complete:
        df_mean, df_sd = _mean_sd([r.delta_f for r in complete])
        note = f"delta_f aggregated over {len(complete)} complete realization(s)"
    else:
        df_mean, df_sd = None, None
        note = "no complete realization: delta_f unavailable (all curves flagged incomplete)"

    return ConditionSummary(
        label=label,
        mode=mode,
        n_realizations=len(results),
        n_complete=len(complete),
        n_incomplete=len(incomplete),
        G_c_mean=G_c_mean,
        G_c_sd=G_c_sd,
        T_max_mean=T_mean,
        T_max_sd=T_sd,
        delta_peak_mean=dp_mean,
        delta_peak_sd=dp_sd,
        K0_mean=k_mean,
        K0_sd=k_sd,
        delta_f_mean=df_mean,
        delta_f_sd=df_sd,
        all_complete=not incomplete,
        incomplete_sources=[r.source for r in incomplete],
        per_realization=[r.as_dict() for r in results],
        delta_f_note=note,
    )


def aggregate_by_mode(results, label="condition"):
    """Split CurveResults by mode ('I' normal, 'II' shear) and aggregate each."""
    out = {}
    for mode in sorted({r.mode for r in results}):
        out[mode] = aggregate([r for r in results if r.mode == mode], label=label)
    return out


def extract_paths(paths, label="condition", **extract_kwargs):
    """Load every realization from ``paths`` (JSON/CSV), extract, aggregate per mode.

    Returns dict mode -> ConditionSummary.
    """
    results = []
    for p in paths:
        for curve in load_realizations(p):
            results.append(
                extract_curve(
                    curve["delta"],
                    curve["traction"],
                    mode=curve["mode"],
                    source=curve["source"],
                    realization=curve["realization"],
                    units=curve["units"],
                    **extract_kwargs,
                )
            )
    if not results:
        raise ValueError(f"no curves found in {list(paths)}")
    return aggregate_by_mode(results, label=label)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _cli(argv=None):
    parser = argparse.ArgumentParser(
        prog="extract_cohesive",
        description="Extract cohesive-zone parameters from network T(delta) curves.",
    )
    parser.add_argument("curves", nargs="+", help="JSON/CSV curve files (>=1)")
    parser.add_argument("--label", default="condition", help="condition label")
    parser.add_argument(
        "--decay-threshold", type=float, default=DEFAULT_DECAY_THRESHOLD,
        help="fraction of T_max counting as failed (default %(default)s)",
    )
    parser.add_argument("--json", help="write summary JSON here")
    parser.add_argument(
        "--moose", metavar="OUT",
        help="also render the MOOSE CZM parameter template to OUT",
    )
    args = parser.parse_args(argv)

    summaries = extract_paths(
        args.curves, label=args.label, decay_threshold=args.decay_threshold
    )
    payload = {mode: s.as_dict() for mode, s in summaries.items()}
    text = json.dumps(payload, indent=2)
    if args.json:
        Path(args.json).write_text(text + "\n")
    print(text)
    if args.moose:
        from . import moose_template

        Path(args.moose).write_text(
            moose_template.render_moose_czm_input(
                args.label, summaries.get("I"), summaries.get("II")
            )
        )
        print(f"\nMOOSE template written to {args.moose}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
