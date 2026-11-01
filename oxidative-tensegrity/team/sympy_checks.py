#!/usr/bin/env python3
"""Symbolic checks (sympy) of the closed forms the team's validators and reviews rely on.

Each check derives a formula from first principles and compares it with the expression used in code or text.
  python3 team/sympy_checks.py      -> prints and writes team/sympy_checks.json
"""
import json
from pathlib import Path

import sympy as sp


def series_chain():
    """jobs.fibril_analytic: M segments (k_m) in series with M interfaces (k_f): slope 1/(M/k_m + M/k_f);
    pull-out work = elastic energy at F_y plus F_y * delta_end; displacement at pull-out = F_y/slope + delta_end."""
    M, km, kf, Fy, de, F = sp.symbols("M k_m k_f F_y delta_end F", positive=True)
    U = M * F / km + M * F / kf
    slope = sp.simplify(F / U)
    used_slope = 1 / (M / km + M / kf)
    W_el = sp.integrate(F, (F, 0, Fy)) / slope  # integral of F dU with dU = dF/slope
    U_fail = U.subs(F, Fy) + de
    return dict(slope_ok=sp.simplify(slope - used_slope) == 0,
                work_ok=sp.simplify(W_el + Fy * de - (Fy ** 2 / (2 * used_slope) + Fy * de)) == 0,
                U_fail_ok=sp.simplify(U_fail - (Fy / used_slope + de)) == 0)


def hill_inflection():
    """Review claim: x^2/(x^2+K^2) changes curvature at x = K/sqrt(3) (sign of the spread effect on mean YAP)."""
    x, K = sp.symbols("x K", positive=True)
    f = x ** 2 / (x ** 2 + K ** 2)
    roots = sp.solve(sp.Eq(sp.diff(f, x, 2), 0), x)
    return dict(inflection=[str(r) for r in roots], claim_ok=any(sp.simplify(r - K / sp.sqrt(3)) == 0 for r in roots),
                yap_at_inflection=str(sp.simplify(f.subs(x, K / sp.sqrt(3)))))


def biot_drainage():
    """jobs.poro_timescale: consolidation coefficient c = k H_A / eta, tau = L^2 / c; dimensions check in SI."""
    m, s, kg = sp.symbols("m s kg", positive=True)
    Pa = kg / (m * s ** 2)
    k, HA, eta, L = m ** 2, Pa, Pa * s, m
    c = k * HA / eta
    tau = L ** 2 / c
    return dict(c_units=str(sp.simplify(c)), tau_units=str(sp.simplify(tau)), ok=sp.simplify(tau / s) == 1)


def wham_jacobian():
    """analyze.py: for a 3D distance, P(r) ~ r^2 exp(-W/kT), so W = -kT ln P + 2 kT ln r (the +2 ln r term)."""
    r, kT, W = sp.symbols("r kT W", positive=True)
    P = r ** 2 * sp.exp(-W / kT)
    return dict(ok=sp.simplify(-kT * sp.log(P) + 2 * kT * sp.log(r) - W) == 0)


def binding_constant():
    """analyze.py unbiased route: one pair in volume V, bound fraction p -> K = V p/(1-p) (pair-in-box mass action)."""
    V, p, K = sp.symbols("V p K", positive=True)
    # relative-coordinate partition functions: bound region contributes K, unbound region ~V, so p = K/(K + V).
    # (Treating one molecule each as independent concentrations would wrongly give V p/(1-p)^2.)
    K_expr = sp.solve(sp.Eq(p, K / (K + V)), K)[0]
    return dict(derived=str(sp.simplify(K_expr)), ok=sp.simplify(K_expr - V * p / (1 - p)) == 0)


if __name__ == "__main__":
    res = dict(series_chain=series_chain(), hill_inflection=hill_inflection(), biot_drainage=biot_drainage(),
               wham_jacobian=wham_jacobian(), binding_constant=binding_constant())
    res = json.loads(json.dumps(res, default=str))
    Path(__file__).with_name("sympy_checks.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
