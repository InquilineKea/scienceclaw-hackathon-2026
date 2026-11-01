"""Dependency-free, fail-closed E2 normalization shared by solver and atlas."""
import math
from numbers import Real
from statistics import median

def matched_stiffness_scale(initial, target, relative_floor=1e-8, max_scale=1e4):
    values = (initial, target, relative_floor, max_scale)
    if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) for v in values):
        raise ValueError("finite numeric modulus and matching settings required")
    if target <= 0 or relative_floor < 0 or max_scale < 1:
        raise ValueError("positive target, nonnegative floor and max_scale >= 1 required")
    if initial <= max(1e-12, relative_floor * target):
        raise ValueError("initial modulus is negative, zero or unresolved")
    scale = target / initial
    if not math.isfinite(scale) or not 1 / max_scale <= scale <= max_scale:
        raise ValueError("stiffness matching requires an excessive scale")
    return float(scale)

def assess_e2(initial, target):
    try:
        return dict(scale=matched_stiffness_scale(initial, target), e2_status="accepted", e2_reason="")
    except (ValueError, TypeError, OverflowError) as exc:
        return dict(scale=None, e2_status="rejected", e2_reason=str(exc))

def derive_e2_rows(rows, target, scaled_fields):
    """Retain rejected rows explicitly; never manufacture normalized mechanics."""
    out = []
    for row in rows:
        gate = assess_e2(row.get("G"), target)
        r = dict(row, control="E2", **gate,
                 e2_method="posthoc_uniform_stiffness_scaling_not_rerun")
        if not row.get("ok", False):
            r.update(scale=None, e2_status="rejected", e2_reason="E1 row is not accepted")
        if r["e2_status"] == "accepted":
            # Nonfinite derived observables must not leak NaN/Infinity into reports.
            for key in scaled_fields:
                value = row.get(key)
                if value is not None and (not isinstance(value, Real) or not math.isfinite(value) or not math.isfinite(value*r["scale"])):
                    r.update(scale=None, e2_status="rejected", e2_reason="nonfinite scaled observable: "+key)
                    break
        for key in scaled_fields:
            value = row.get(key)
            r[key] = value*r["scale"] if r["e2_status"] == "accepted" and value is not None else None
        r["ok"] = bool(row.get("ok", False) and r["e2_status"] == "accepted")
        out.append(r)
    return out

def select_e2_target(moduli, is_baseline):
    if not is_baseline:
        raise ValueError("designated E2 baseline unavailable; no fallback target")
    if not moduli:
        raise ValueError("designated E2 baseline has no matched specimens")
    for item in moduli:
        matched_stiffness_scale(item["G"], item["G"])
    target = float(median(item["G"] for item in moduli))
    matched_stiffness_scale(target, target)
    return target

def derive_e2_curve(traction, peak, gc, initial, target, e1_ok):
    """Validate the curve export independently of the tabular E2 path."""
    gate = assess_e2(initial, target)
    result = dict(status=gate["e2_status"], reason=gate["e2_reason"],
                  method="posthoc_uniform_stiffness_scaling_not_rerun")
    if e1_ok is not True:
        result.update(status="rejected", reason="E1 row is not accepted")
        return result
    if gate["e2_status"] != "accepted":
        return result
    try:
        values = list(traction) + [peak, gc]
        if not values[:-2] or any(isinstance(v,bool) or not isinstance(v,Real) or not math.isfinite(v) for v in values):
            raise ValueError("invalid or nonfinite fracture observable")
        scaled = [float(v*gate["scale"]) for v in values]
        if any(not math.isfinite(v) for v in scaled):
            raise ValueError("nonfinite scaled fracture observable")
    except (ValueError,TypeError,OverflowError) as exc:
        result.update(status="rejected", reason=str(exc))
        return result
    result.update(scale=gate["scale"], traction=scaled[:-2], T_peak=scaled[-2], Gc=scaled[-1])
    return result
