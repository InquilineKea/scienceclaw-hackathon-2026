#!/usr/bin/env python3
"""Perturb the existing organoid YAP/PS->LOX/MMP14 remodelling loop.

Frozen-radius, zero-strain slice of oxt/organoid.py: gene kinetics and matrix
update are identical, while the cell response is interpolated from the saved
flat-E cell calibration. This tests a local feedback mechanism, not collective
morphological memory. No shared model file is modified.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np
from oxt.organoid import GENES, OrganoidParams, gene_targets

ROOT = Path(__file__).resolve().parent


def calibration(path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    e = np.array([float(r['E_Pa']) for r in rows])
    y = np.array([float(r['Y']) for r in rows])
    ps = np.array([float(r['prestress_ratio']) for r in rows])
    order = np.argsort(e)
    return np.log(e[order]), y[order], ps[order]


def run(tab, base_e, dose, init, pulse, days, bounds, dt=0.2, memory=True):
    p = OrganoidParams()
    loge, ys, pss = tab
    lo, hi = np.log(bounds)
    s = float(init)
    genes = {g: 0.0 for g in GENES}
    history = []
    steps = round(days * 24 / dt)
    pulse_start, pulse_end, pulse_amplitude = pulse
    for t in range(steps + 1):
        day = t * dt / 24
        # External stiffness stimulus is transient and is removed exactly at pulse_end.
        ext = pulse_amplitude if pulse_start <= day < pulse_end else 0.0
        x = np.log(base_e) + s + ext
        ym = float(np.interp(x, loge, ys))
        ps = float(np.interp(x, loge, pss))
        yeff = ym / (1 + genes['AMOTL2'] / p.k_amotl2)
        target = gene_targets(yeff, ps, 0.7)
        if t == 0:
            # Match current simulate_organoids' initial gene equilibration.
            for _ in range(60):
                yeff = ym / (1 + genes['AMOTL2'] / p.k_amotl2)
                target = gene_targets(yeff, ps, 0.7)
                for g in GENES:
                    genes[g] = 0.5 * (genes[g] + float(target[g]))
        rate = p.k_lox_per_day * genes['LOX'] - p.k_mmp_per_day * math.exp(-2.5 * dose) * genes['MMP14']
        if t % round(24 / dt) == 0:
            history.append(dict(day=round(day, 5), logS=s, Y=yeff, PS=ps, rate_per_day=rate,
                                at_bound=abs(s-lo)<1e-6 or abs(s-hi)<1e-6, stimulus=ext))
        if t == steps:
            break
        for g, (_, _, _, tau) in GENES.items():
            genes[g] += dt / tau * (float(target[g]) - genes[g])
        s += dt / 24 * rate
        if bounds is not None:
            s = float(np.clip(s, lo, hi))
    return history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=ROOT/'results/setpoint_vs_scar')
    ap.add_argument('--days', type=float, default=90)
    ap.add_argument('--dt', type=float, default=0.2)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    tab = calibration(ROOT/'results/topo/yap_calibration.csv')
    curves = []
    summary = []
    # E=180 Pa lies in the saved cell model's 25-75% YAP band.
    for dose in (0.0, 1.0):
        for bounds in ((0.4, 2.5), (0.1, 10.0)):
            for init in (math.log(0.7), 0.0, math.log(1.4)):
                for amplitude in (-math.log(1.8), 0.0, math.log(1.8)):
                    pulse = (10, 13, amplitude)
                    h = run(tab, 180.0, dose, init, pulse, args.days, bounds, dt=args.dt)
                    key = dict(dose=dose, bounds=f'{bounds[0]}:{bounds[1]}', init_logS=init,
                               pulse_logE=amplitude)
                    for row in h:
                        curves.append(dict(**key, **row))
                    early = next(r for r in h if r['day'] >= 30)
                    late = h[-1]
                    summary.append(dict(**key, final_logS=late['logS'], day30_logS=early['logS'],
                                        late_rate_per_day=late['rate_per_day'], at_bound=late['at_bound'],
                                        drift_30_to_final=late['logS']-early['logS']))
    for name, rows in [('trajectories.csv',curves),('summary.csv',summary)]:
        with (args.out/name).open('w', newline='') as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (args.out/'run.json').write_text(json.dumps({'days':args.days,'dt_h':args.dt,'conditions':len(summary),
        'calibration':'results/topo/yap_calibration.csv','base_E_Pa':180,
        'scope':'frozen-radius local loop; not a full organoid or collective simulation'},indent=2))
    print(json.dumps({'conditions':len(summary),'out':str(args.out)}))


if __name__ == '__main__':
    main()
