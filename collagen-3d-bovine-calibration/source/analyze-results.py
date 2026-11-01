#!/usr/bin/env python3
"""Original standard-library analysis of completed 3D CPU JSON outputs.

No numerical package or solver import. Default primary resolutions are25/50;
use --coarse-steps 100 --fine-steps 200 for preserved higher-resolution controls.
Default outputs go to analysis/ so the
existing bovine fit summary.json is preserved. Missing cases and failed gates
remain visible. Run --self-test for original synthetic gate checks only.
"""
import argparse
import collections
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parent
SEEDS = (29, 30, 31, 32)
PLANES = (1, 2)
THRESHOLDS = (0.1, 0.2)
CONFIGS = (('baseline', 0.0), ('clustered', 0.15), ('distributed', 0.15),
           ('clustered', 0.3), ('distributed', 0.3))
RESOLUTIONS = (25, 50)
STEP_LIMIT = 0.05
ENERGY_LIMIT = 0.02
FORCE_LIMIT = 1e-7
CAP = 0.5
STRICT_STABILITY = 'positive_curvature_at_checked_state'
MARGINAL_STABILITY = 'no_resolved_negative_curvature_marginal'
EXPECTED_LABELS = {'initial_state', 'peak_state', 'terminal_state'}


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def number(x):
    return float(x) if finite(x) else None


def scaled(x, factor):
    return float(x) * factor if finite(x) and finite(factor) else None


def rel_change(coarse, fine):
    if not finite(coarse) or not finite(fine):
        return None
    return abs(coarse-fine)/max(abs(fine), 1e-12)


def passes(x, limit):
    return finite(x) and x <= limit


def ratio(a, b):
    return a/b if finite(a) and finite(b) and abs(b) > 1e-12 else None


def difference(a, b):
    return a-b if finite(a) and finite(b) else None

def sign_agreement(coarse_difference, fine_difference):
    if not finite(coarse_difference) or not finite(fine_difference):
        return None, 'missing_resolution_contrast'
    sign = lambda x: (x > 0) - (x < 0)
    a, b = sign(coarse_difference), sign(fine_difference)
    if a == b == 0:
        return True, 'both_zero_no_rank_difference'
    if a == b:
        return True, 'same_nonzero_direction'
    if a == 0 or b == 0:
        return False, 'zero_vs_nonzero_resolution_sensitive'
    return False, 'opposite_directions_resolution_sensitive'


def mean(values):
    values = [x for x in values if finite(x)]
    return statistics.fmean(values) if values else None


def extent(values):
    values = [x for x in values if finite(x)]
    return [min(values), max(values)] if values else None


def safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(x) for x in value]
    return value


def dump(path, obj):
    path.write_text(json.dumps(safe(obj), indent=2, allow_nan=False)+'\n')


def csvout(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    if not fields:
        path.write_text('')
        return
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(safe(v), separators=(',', ':'))
                        if isinstance(v, (dict, list, tuple)) else safe(v)
                        for k, v in row.items()})


def key_of(d, fallback=None):
    try:
        return (int(d['seed']), int(d['plane']), round(float(d['threshold']), 8),
                str(d['pattern']), round(float(d['density']), 8), int(d['steps']))
    except (KeyError, TypeError, ValueError):
        if fallback:
            m = re.search(r's(\d+)-seed(\d+)-p(\d+)-t([0-9.]+)-(baseline|clustered|distributed)-([0-9.]+)', fallback)
            if m:
                return (int(m[2]), int(m[3]), round(float(m[4]), 8), m[5],
                        round(float(m[6].rstrip('.')), 8), int(m[1]))
    return None


def meta(k):
    return dict(zip(('seed', 'plane', 'threshold', 'pattern', 'density', 'steps'), k))


def expected_keys():
    return {(s, p, t, pat, den, n)
            for s, p, t, (pat, den), n in itertools.product(
                SEEDS, PLANES, THRESHOLDS, CONFIGS, RESOLUTIONS)}


def calibration_map(path):
    raw = json.loads(path.read_text())
    if isinstance(raw, dict):
        raw = raw.get('calibration', raw.get('records', raw.get('seeds', [])))
    rows = {}
    for d in raw:
        seed = int(d['seed'])
        planes = d.get('planes', [])
        reasons = []
        if {x.get('plane') for x in planes} != set(PLANES):
            reasons.append('missing_or_unexpected_calibration_plane')
        for x in planes:
            if x.get('accepted') is not True:
                reasons.append('amplitude_plane_not_accepted')
            if not passes(x.get('maxResidual'), FORCE_LIMIT):
                reasons.append('amplitude_plane_force_gate')
        factor = number(d.get('scale_Pa'))
        if factor is None or factor <= 0:
            reasons.append('nonpositive_or_missing_scale')
        rows[seed] = dict(seed=seed, scale_Pa=factor, accepted=not reasons,
                          reasons=sorted(set(reasons)),
                          G_model_at_1pct=number(d.get('G')),
                          relative_amplitude_change=number(d.get('relative_change_from_smallstrain')),
                          planes=[{k: x.get(k) for k in ('plane', 'G_storage', 'accepted', 'maxResidual')}
                                  for x in planes])
    return rows


def stability_audit(d, fine):
    checks = d.get('selected_state_stability')
    if not fine:
        return dict(level='not_requested_at_coarse_resolution', strict=False,
                    conditional=False, labels=[], classifications=[], checks=[])
    if not isinstance(checks, list) or not checks:
        return dict(level='unqualified_missing_checks', strict=False, conditional=False,
                    labels=[], classifications=[], checks=[])
    labels = [x.get('label') for x in checks]
    classifications = [x.get('classification', 'missing_classification') for x in checks]
    complete = set(labels) == EXPECTED_LABELS and len(labels) == len(EXPECTED_LABELS)
    gradient_ok = all(passes(x.get('max_free_gradient'), FORCE_LIMIT) for x in checks)
    allowed = all(x in (STRICT_STABILITY, MARGINAL_STABILITY) for x in classifications)
    conditional = complete and gradient_ok and allowed
    strict = conditional and all(x == STRICT_STABILITY for x in classifications)
    level = ('positive_at_three_checked_states' if strict else
             'marginal_no_resolved_negative_at_three_checked_states' if conditional else
             'unqualified_negative_unresolved_or_incomplete_checks')
    keep = ('label', 'gamma', 'classification', 'max_free_gradient',
            'minimum_scaled_eigenvalue', 'maximum_scaled_eigenvalue',
            'negative_cutoff', 'negative_eigenvalues_below_cutoff',
            'symmetry_error', 'relative_hvp_error', 'weakest_direction_curvatures')
    return dict(level=level, strict=strict, conditional=conditional, labels=labels,
                classifications=classifications,
                checks=[{k: x.get(k) for k in keep if k in x} for x in checks])


def audit_record(d, key, cal):
    frames = d.get('frames', [])
    good = [f for f in frames if f.get('accepted') is True]
    last = good[-1] if good else {}
    factor = cal.get(key[0], {}).get('scale_Pa')
    calibration_ok = cal.get(key[0], {}).get('accepted') is True
    grid_complete = (len(frames) == key[-1]+1 and all(finite(f.get('gamma')) and abs(f['gamma']-CAP*i/key[-1]) <= 1e-10 for i,f in enumerate(frames)))
    complete = (grid_complete and d.get('trajectoryComplete') is True and d.get('status') == 'converged'
                and bool(frames) and len(good) == len(frames)
                and finite(last.get('gamma')) and last['gamma'] >= CAP-1e-12)
    max_force = max((f['residual'] for f in good if finite(f.get('residual'))), default=None)
    force_ok = (complete and max_force is not None and max_force <= FORCE_LIMIT
                and all(finite(f.get('residual')) for f in good))
    terminal_error = number(d.get('terminalRelativeEnergyError'))
    recomputed = None
    if all(finite(last.get(k)) for k in ('work', 'energy', 'removedEnergy', 'relaxEnergy')):
        recomputed = abs(last['work']-last['energy']-last['removedEnergy']-
                         last['relaxEnergy'])/max(abs(last['work']), 1e-12)
    discrepancy = abs(terminal_error-recomputed) if finite(terminal_error) and finite(recomputed) else None
    # A missing bookkeeping field fails qualification rather than silently passing.
    loss_ok = bool(good)
    previous = {'removedEnergy': 0.0, 'relaxEnergy': 0.0}
    for f in good:
        floor = 1e-10*max(1.0, abs(f.get('work', 0)) if finite(f.get('work')) else 1)
        for k in previous:
            value = f.get(k)
            if not finite(value) or value < -floor or value < previous[k]-floor:
                loss_ok = False
            if finite(value):
                previous[k] = value
    energy_ok = (complete and passes(terminal_error, ENERGY_LIMIT)
                 and passes(recomputed, ENERGY_LIMIT) and passes(discrepancy, 1e-8) and loss_ok)
    resolved = d.get('peakResolved') is True and complete
    right_censored = d.get('peakRightCensored') is True
    endpoint = ('incomplete_or_unresolved_trajectory' if not complete else
                'resolved_peak_and_postpeak_drop' if resolved else
                'right_censored_maximum_at_cap' if right_censored else
                'peak_not_resolved_by_postpeak_criterion')
    first_damage = None
    previous_gamma = 0.0
    for f in good:
        if finite(f.get('damage')) and f['damage'] > 0:
            first_damage = [previous_gamma, f['gamma']]
            break
        previous_gamma = f.get('gamma', previous_gamma)
    stability = stability_audit(d, key[-1] == RESOLUTIONS[1])
    row = dict(**meta(key), source_file=d.get('_source_file'), status=d.get('status'),
               frames=len(frames), accepted_frames=len(good), expected_frames=key[-1]+1, strain_grid_complete=grid_complete, trajectory_complete=complete,
               calibration_accepted=calibration_ok, scale_Pa=factor if calibration_ok else None,
               max_free_gradient_model_units=max_force, force_gate=force_ok,
               terminal_relative_energy_error=terminal_error,
               recomputed_terminal_relative_energy_error=recomputed,
               energy_bookkeeping_discrepancy=discrepancy, irreversible_loss_gate=loss_ok,
               energy_gate=energy_ok, endpoint_class=endpoint, peak_resolved=resolved,
               peak_right_censored=right_censored, stability_level=stability['level'],
               stability_strict=stability['strict'], stability_conditional=stability['conditional'],
               stability_classifications=stability['classifications'],
               maximum_observed_stress_model=number(d.get('peakStress')),
               maximum_observed_stress_Pa=scaled(d.get('peakStress'), factor) if calibration_ok else None,
               observed_maximum_gamma=number(d.get('peakGamma')),
               resolved_peak_stress_Pa=scaled(d.get('peakStress'), factor) if calibration_ok and resolved else None,
               work_through_cap_J_m3=scaled(d.get('workThroughCap'), factor) if calibration_ok and complete else None,
               work_to_resolved_peak_J_m3=scaled(d.get('workToPeak'), factor) if calibration_ok and resolved else None,
               work_through_last_accepted_J_m3=scaled(d.get('workThroughLastAccepted'), factor) if calibration_ok else None,
               last_accepted_gamma=number(last.get('gamma')), last_damage_fraction=number(last.get('damage')),
               damage_at_cap=number(last.get('damage')) if complete else None,
               broken_edge_count_at_cap=round(last['damage']*d['edges']) if complete and finite(last.get('damage')) and finite(d.get('edges')) else None,
               first_damage_strain_bracket=first_damage, nodes=d.get('nodes'), edges=d.get('edges'),
               realized_coordination=d.get('z'), locked_junction_count=d.get('lock_count'),
               locking_spatial_spread=d.get('lock_spread'), seconds=number(d.get('seconds')))
    return row, stability


def resolution_pair(key5, coarse, fine):
    r = dict(zip(('seed', 'plane', 'threshold', 'pattern', 'density'), key5))
    r.update(coarse_present=coarse is not None, fine_present=fine is not None)
    if coarse is None or fine is None:
        r.update(step_maximum_stress_gate=False, step_work_through_cap_gate=False,
                 step_work_to_resolved_peak_gate=False, numerical_qualified_strict=False,
                 numerical_qualified_conditional=False, fracture_endpoint_qualified_strict=False,
                 fracture_endpoint_qualified_conditional=False, qualification='missing_resolution')
        return r
    ds = rel_change(coarse['maximum_observed_stress_model'], fine['maximum_observed_stress_model'])
    dw = rel_change(coarse['work_through_cap_J_m3'], fine['work_through_cap_J_m3'])
    dp = rel_change(coarse['work_to_resolved_peak_J_m3'], fine['work_to_resolved_peak_J_m3'])
    common = all(x['trajectory_complete'] and x['force_gate'] and x['energy_gate']
                 and x['calibration_accepted'] for x in (coarse, fine))
    base = common and passes(ds, STEP_LIMIT) and passes(dw, STEP_LIMIT)
    strict = base and fine['stability_strict']
    conditional = base and fine['stability_conditional']
    fracture_common = (coarse['peak_resolved'] and fine['peak_resolved']
                       and not coarse['peak_right_censored'] and not fine['peak_right_censored']
                       and passes(dp, STEP_LIMIT))
    r.update(maximum_stress_relative_step_difference=ds,
             work_through_cap_relative_step_difference=dw,
             work_to_resolved_peak_relative_step_difference=dp,
             step_maximum_stress_gate=passes(ds, STEP_LIMIT),
             step_work_through_cap_gate=passes(dw, STEP_LIMIT),
             step_work_to_resolved_peak_gate=passes(dp, STEP_LIMIT),
             both_complete=all(x['trajectory_complete'] for x in (coarse, fine)),
             both_energy_qualified=all(x['energy_gate'] for x in (coarse, fine)),
             both_calibration_qualified=all(x['calibration_accepted'] for x in (coarse, fine)),
             fine_stability_level=fine['stability_level'],
             both_resolved_peak=coarse['peak_resolved'] and fine['peak_resolved'],
             coarse_endpoint_class=coarse['endpoint_class'], fine_endpoint_class=fine['endpoint_class'],
             numerical_qualified_strict=strict, numerical_qualified_conditional=conditional,
             fracture_endpoint_qualified_strict=strict and fracture_common,
             fracture_endpoint_qualified_conditional=conditional and fracture_common,
             qualification=('qualified_positive_checked_states' if strict else
                            'conditional_marginal_checked_states_not_stability_proof' if conditional else
                            'unqualified'),
             fine_maximum_observed_stress_Pa=fine['maximum_observed_stress_Pa'],
             fine_work_through_cap_J_m3=fine['work_through_cap_J_m3'],
             fine_work_to_resolved_peak_J_m3=fine['work_to_resolved_peak_J_m3'],
             coarse_damage_at_cap=coarse['damage_at_cap'],
             fine_damage_at_cap=fine['damage_at_cap'],
             damage_fraction_absolute_step_difference=abs(coarse['damage_at_cap']-fine['damage_at_cap']) if finite(coarse['damage_at_cap']) and finite(fine['damage_at_cap']) else None,
             damage_percentage_point_absolute_step_difference=100*abs(coarse['damage_at_cap']-fine['damage_at_cap']) if finite(coarse['damage_at_cap']) and finite(fine['damage_at_cap']) else None,
             coarse_broken_edge_count=round(coarse['damage_at_cap']*coarse['edges']) if finite(coarse['damage_at_cap']) and finite(coarse.get('edges')) else None,
             fine_broken_edge_count=round(fine['damage_at_cap']*fine['edges']) if finite(fine['damage_at_cap']) and finite(fine.get('edges')) else None,
             damage_precision_tolerance_prespecified=False)
    return r


def seed_aggregate(pairs, group_fields, tier):
    """Equal seed weights; both prespecified angles required for primary mean."""
    groups = collections.defaultdict(list)
    for row in pairs:
        groups[tuple(row.get(k) for k in group_fields)].append(row)
    result = []
    for key, rows in sorted(groups.items(), key=lambda kv: str(kv[0])):
        per_seed = []
        for seed in SEEDS:
            all_angles = [r for r in rows if r['seed'] == seed]
            selected = [r for r in all_angles if r.get(tier) is True and finite(r.get('difference'))]
            complete = len(selected) == len(PLANES) and {r['plane'] for r in selected} == set(PLANES)
            per_seed.append(dict(seed=seed, available_angle_records=len(all_angles),
                                 qualified_angles=len(selected), complete_two_angle_pair=complete,
                                 available_angle_mean_difference=mean(r.get('difference') for r in selected),
                                 available_angle_mean_ratio=mean(r.get('ratio') for r in selected),
                                 complete_angle_mean_difference=mean(r.get('difference') for r in selected) if complete else None,
                                 complete_angle_mean_ratio=mean(r.get('ratio') for r in selected) if complete else None,
                                 angle_difference_range=extent(r.get('difference') for r in selected)))
        valid = [r for r in per_seed if r['complete_two_angle_pair']]
        values = [r['complete_angle_mean_difference'] for r in valid]
        ratios = [r['complete_angle_mean_ratio'] for r in valid if finite(r['complete_angle_mean_ratio'])]
        out = dict(zip(group_fields, key))
        out.update(qualification_tier=tier, expected_seeds=len(SEEDS),
                   seeds_with_both_angles=len(valid), paired_angle_records=sum(r['qualified_angles'] for r in per_seed),
                   mean_of_seed_mean_differences=mean(values), seed_mean_difference_range=extent(values),
                   mean_of_seed_mean_ratios=mean(ratios), seed_mean_ratio_range=extent(ratios),
                   seed_signs=dict(positive=sum(x > 0 for x in values), negative=sum(x < 0 for x in values),
                                   zero=sum(x == 0 for x in values)),
                   per_seed=per_seed,
                   uncertainty='Descriptive four-seed analysis; angles and strain frames are not independent replicates.')
        result.append(out)
    return result


def placement_pairs(rows, resolution):
    out = []
    metrics = [('maximum_observed_stress_Pa', False), ('work_through_cap_J_m3', False),
               ('work_to_resolved_peak_J_m3', True), ('resolved_peak_stress_Pa', True),
               ('damage_at_cap', False)]
    for seed, plane, threshold, den in itertools.product(SEEDS, PLANES, THRESHOLDS, (0.15, 0.3)):
        ck = (seed, plane, threshold, 'clustered', den)
        dk = (seed, plane, threshold, 'distributed', den)
        c, d = rows.get(ck+(RESOLUTIONS[1],)), rows.get(dk+(RESOLUTIONS[1],))
        cp, dp = resolution[ck], resolution[dk]
        coarse_c, coarse_d = rows.get(ck+(RESOLUTIONS[0],)), rows.get(dk+(RESOLUTIONS[0],))
        for metric, fracture in metrics:
            cv, dv = (c.get(metric) if c else None), (d.get(metric) if d else None)
            gate = 'fracture_endpoint_qualified_' if fracture else 'numerical_qualified_'
            coarse_cv = coarse_c.get(metric) if coarse_c else None
            coarse_dv = coarse_d.get(metric) if coarse_d else None
            coarse_contrast = difference(coarse_cv, coarse_dv)
            fine_contrast = difference(cv, dv)
            agrees, agreement_label = sign_agreement(coarse_contrast, fine_contrast)
            strict = bool(cp.get(gate+'strict') and dp.get(gate+'strict'))
            conditional = bool(cp.get(gate+'conditional') and dp.get(gate+'conditional'))
            out.append(dict(seed=seed, plane=plane, threshold=threshold, density=den, metric=metric,
                            contrast='clustered_minus_distributed', clustered=cv, distributed=dv,
                            difference=fine_contrast, ratio=ratio(cv, dv),
                            coarse_clustered=coarse_cv, coarse_distributed=coarse_dv,
                            coarse_difference=coarse_contrast, fine_difference=fine_contrast,
                            contrast_direction_agrees_both_resolutions=agrees, contrast_direction_resolution_label=agreement_label,
                            damage_rank_qualified_strict=bool(metric=='damage_at_cap' and strict and agrees is True),
                            damage_rank_qualified_conditional=bool(metric=='damage_at_cap' and conditional and agrees is True),
                            damage_precision_tolerance_prespecified=False if metric=='damage_at_cap' else None,
                            descriptive=finite(cv) and finite(dv),
                            qualified_strict=strict,
                            qualified_conditional=conditional,
                            clustered_endpoint_class=c.get('endpoint_class') if c else 'missing',
                            distributed_endpoint_class=d.get('endpoint_class') if d else 'missing',
                            clustered_qualification=cp.get('qualification'),
                            distributed_qualification=dp.get('qualification')))
    return out


def baseline_pairs(rows, resolution):
    out = []
    for seed, plane, threshold, (pat, den) in itertools.product(SEEDS, PLANES, THRESHOLDS, CONFIGS[1:]):
        k = (seed, plane, threshold, pat, den)
        bkey = (seed, plane, threshold, 'baseline', 0.0)
        a, b = rows.get(k+(RESOLUTIONS[1],)), rows.get(bkey+(RESOLUTIONS[1],))
        for metric, fracture in [('maximum_observed_stress_Pa', False), ('work_through_cap_J_m3', False),
                                 ('work_to_resolved_peak_J_m3', True), ('resolved_peak_stress_Pa', True)]:
            av, bv = a.get(metric) if a else None, b.get(metric) if b else None
            gate = 'fracture_endpoint_qualified_' if fracture else 'numerical_qualified_'
            out.append(dict(seed=seed, plane=plane, threshold=threshold, pattern=pat, density=den,
                            metric=metric, contrast='locking_minus_same_threshold_baseline',
                            locking=av, baseline=bv, difference=difference(av, bv), ratio=ratio(av, bv),
                            descriptive=finite(av) and finite(bv),
                            qualified_strict=bool(resolution[k].get(gate+'strict') and resolution[bkey].get(gate+'strict')),
                            qualified_conditional=bool(resolution[k].get(gate+'conditional') and resolution[bkey].get(gate+'conditional'))))
    return out


def stiffness_analysis(path, cal):
    if not path.exists():
        return dict(source_present=False, rows=[], paired=[], aggregates=[])
    raw = json.loads(path.read_text())
    if isinstance(raw, dict):
        raw = raw.get('rows', raw.get('records', []))
    rows = []
    for x in raw:
        seed = int(x['seed']); factor = cal.get(seed, {}).get('scale_Pa')
        accepted = x.get('accepted') is True and passes(x.get('residual'), FORCE_LIMIT)
        calibrated = accepted and cal.get(seed, {}).get('accepted') is True
        rows.append(dict(seed=seed, plane=int(x['plane']), pattern=x['pattern'], density=float(x['density']),
                         G_model=number(x.get('G_dim')), G_Pa=scaled(x.get('G_dim'), factor) if calibrated else None,
                         accepted=accepted, calibration_accepted=cal.get(seed, {}).get('accepted') is True,
                         scale_Pa=factor if calibrated else None, source_G_Pa=number(x.get('G_Pa')),
                         locked_junction_count=x.get('locked'), spread=x.get('spread'),
                         residual_model_units=number(x.get('residual'))))
    lookup = {(x['seed'], x['plane'], x['pattern'], round(x['density'], 8)): x for x in rows}
    paired = []
    for seed, plane, den in itertools.product(SEEDS, PLANES, (0.15, 0.3)):
        c, d = lookup.get((seed, plane, 'clustered', den)), lookup.get((seed, plane, 'distributed', den))
        if not c or not d:
            paired.append(dict(seed=seed, plane=plane, density=den, metric='initial_stiffness_Pa', descriptive=False,
                               qualified_strict=False, difference=None, ratio=None))
            continue
        ok = c['accepted'] and d['accepted'] and c['calibration_accepted'] and d['calibration_accepted']
        paired.append(dict(seed=seed, plane=plane, density=den,
                           contrast='clustered_minus_distributed', metric='initial_stiffness_Pa',
                           clustered_G_Pa=c['G_Pa'], distributed_G_Pa=d['G_Pa'],
                           difference=difference(c['G_Pa'], d['G_Pa']),
                           ratio=ratio(c['G_model'], d['G_model']), descriptive=ok, qualified_strict=ok))
    aggregates = seed_aggregate(paired, ('density', 'metric'), 'qualified_strict')
    return dict(source_present=True, rows=rows, paired=paired, aggregates=aggregates,
                note='G_Pa recomputed from G_dim and final accepted amplitude scale; source_G_Pa retained for audit.')


def analyze(input_dir, outdir, calibration_path, stiffness_path):
    if not input_dir.is_dir():
        raise ValueError('Completed-results directory does not exist: '+str(input_dir))
    if input_dir.resolve() == outdir.resolve():
        raise ValueError('Output directory must differ from the raw input directory.')
    cal = calibration_map(calibration_path)
    expected = expected_keys(); records = {}; errors = []; partials = []; duplicates = []; unexpected = []; hashes = []
    for file in sorted(input_dir.glob('*.json')):
        if file.name.endswith('.partial.json'):
            partials.append(file.name)
            continue
        b = file.read_bytes(); hashes.append(dict(file=file.name, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
        try:
            d = json.loads(b)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(dict(file=file.name, kind='invalid_json', error=str(exc)[:2000], key=key_of({}, file.name)))
            continue
        if not isinstance(d, dict):
            errors.append(dict(file=file.name, kind='nonobject_json', error='Expected a JSON object.'))
            continue
        key = key_of(d, file.name)
        if file.name.endswith('.error.json') or 'error' in d and 'frames' not in d:
            errors.append(dict(file=file.name, kind='explicit_error', error=str(d.get('error', d))[:2000],
                               key=meta(key) if key else None))
            continue
        if key is None or key not in expected:
            unexpected.append(dict(file=file.name, key=meta(key) if key else None))
            continue
        if key in records:
            duplicates.append(dict(key=meta(key), files=[records[key]['_source_file'], file.name]))
            continue
        d['_source_file'] = file.name; records[key] = d
    # Ambiguous duplicated endpoints remain excluded; never silently choose a favorable duplicate.
    duplicate_keys = {key_of(x['key']) for x in duplicates}
    for key in duplicate_keys:
        records.pop(key, None)
    rows = {}; stability = {}; curves = []
    for key, d in sorted(records.items()):
        row, st = audit_record(d, key, cal); rows[key] = row; stability[key] = st
        factor = row['scale_Pa']; frames = []
        for f in d.get('frames', []):
            frame = {k: f.get(k) for k in ('gamma', 'accepted', 'damage', 'avalanche', 'residual', 'relativeEnergyError') if k in f}
            for src, dst in [('stress', 'stress_Pa'), ('preStress', 'pre_avalanche_stress_Pa'),
                             ('energy', 'stored_energy_J_m3'), ('work', 'work_J_m3'),
                             ('removedEnergy', 'deletion_loss_J_m3'), ('relaxEnergy', 'relaxation_loss_J_m3')]:
                frame[src+'_model'] = number(f.get(src))
                frame[dst] = scaled(f.get(src), factor)
            frames.append(frame)
        curves.append(dict(**meta(key), source_file=d['_source_file'], audit=row, selected_state_stability=st,
                           frames=frames, interpretation='Descriptive curve remains accessible even when unqualified.'))
    resolution = {}
    for key in sorted({k[:-1] for k in expected}):
        resolution[key] = resolution_pair(key, rows.get(key+(RESOLUTIONS[0],)), rows.get(key+(RESOLUTIONS[1],)))
    placed = placement_pairs(rows, resolution); baselines = baseline_pairs(rows, resolution)
    placement_aggregates = []; baseline_aggregates = []
    for tier in ('descriptive', 'qualified_conditional', 'qualified_strict'):
        placement_aggregates += seed_aggregate(placed, ('threshold', 'density', 'metric'), tier)
        baseline_aggregates += seed_aggregate(baselines, ('threshold', 'pattern', 'density', 'metric'), tier)
    damage_ranking_aggregates = []
    damage_rows = [r for r in placed if r['metric']=='damage_at_cap']
    for tier in ('damage_rank_qualified_conditional','damage_rank_qualified_strict'):
        damage_ranking_aggregates += seed_aggregate(damage_rows, ('threshold','density','metric'),tier)
    damage_step_values = [r.get('damage_fraction_absolute_step_difference') for r in resolution.values() if finite(r.get('damage_fraction_absolute_step_difference'))]
    damage_diagnostics = dict(resolution_pairs_with_damage_comparison=len(damage_step_values),
                              absolute_damage_fraction_step_difference_range=extent(damage_step_values),
                              mean_absolute_damage_fraction_step_difference=mean(damage_step_values),
                              absolute_damage_percentage_point_step_difference_range=extent(100*x for x in damage_step_values),
                              exact_equal_damage_fraction_pairs=sum(x==0 for x in damage_step_values),
                              placement_direction_counts=dict(collections.Counter(r['contrast_direction_resolution_label'] for r in damage_rows)),
                              precision_tolerance_prespecified=False,
                              interpretation='Stress/work5% gates do not establish damage-fraction precision. Ranking tiers additionally require the clustered-minus-distributed contrast direction to agree at both resolutions; zero/zero means no rank difference. No new numerical tolerance was selected.')
    stiff = stiffness_analysis(stiffness_path, cal)
    missing = sorted(expected-set(records))
    state_classes = collections.Counter(c for st in stability.values() for c in st['classifications'])
    counts = dict(expected_final_cases=len(expected), final_cases_loaded=len(records),
                  missing_final_cases=len(missing), ignored_partial_files=len(partials),
                  explicit_or_parse_errors=len(errors), duplicate_case_keys=len(duplicate_keys),
                  unexpected_files=len(unexpected), expected_resolution_pairs=80,
                  complete_resolution_pairs=sum(r['coarse_present'] and r['fine_present'] for r in resolution.values()),
                  fine_cases_loaded=sum(k[-1] == RESOLUTIONS[1] for k in records),
                  completed_trajectories=sum(r['trajectory_complete'] for r in rows.values()),
                  force_qualified_cases=sum(r['force_gate'] for r in rows.values()),
                  energy_qualified_cases=sum(r['energy_gate'] for r in rows.values()),
                  resolved_peak_cases=sum(r['peak_resolved'] for r in rows.values()),
                  right_censored_cases=sum(r['peak_right_censored'] for r in rows.values()),
                  numerical_qualified_strict_pairs=sum(r.get('numerical_qualified_strict', False) for r in resolution.values()),
                  numerical_qualified_conditional_pairs=sum(r.get('numerical_qualified_conditional', False) for r in resolution.values()),
                  fracture_endpoint_qualified_strict_pairs=sum(r.get('fracture_endpoint_qualified_strict', False) for r in resolution.values()),
                  fracture_endpoint_qualified_conditional_pairs=sum(r.get('fracture_endpoint_qualified_conditional', False) for r in resolution.values()))
    summary = dict(schema=1, scope='Synthetic periodic3D bulk-matched sensitivity; not measured-architecture or chemistry validation',
                   counts=counts, calibration=list(cal.values()),
                   selected_state_stability_classification_counts=dict(state_classes),
                   gates=dict(relative_step_limit=STEP_LIMIT, relative_energy_limit=ENERGY_LIMIT,
                              free_gradient_limit_model_units=FORCE_LIMIT, cap_shear=CAP,
                              fine_stability_labels=sorted(EXPECTED_LABELS), coarse_steps=RESOLUTIONS[0], fine_steps=RESOLUTIONS[1]),
                   missing_cases=[meta(k) for k in missing], errors=errors, duplicate_cases=duplicates,
                   ignored_partial_files=partials, unexpected_files=unexpected,
                   endpoint_counts_by_resolution={str(n):dict(collections.Counter(r['endpoint_class'] for r in rows.values() if r['steps']==n)) for n in RESOLUTIONS},
                   coverage_by_resolution={str(n):dict(loaded=sum(r['steps']==n for r in rows.values()), expected=80) for n in RESOLUTIONS},
                   placement_aggregates=placement_aggregates, baseline_aggregates=baseline_aggregates,
                   stiffness_aggregates=stiff['aggregates'],
                   damage_resolution_diagnostics=damage_diagnostics, damage_ranking_aggregates=damage_ranking_aggregates,
                   interpretation=dict(calibration='Conditional uniform energy-density scale from bovine small-amplitude bulk response; unchanged within seed across interventions.',
                                       units='Stress Pa; energy/work density J/m^3 conditional on the bulk calibration. No physical fracture area or Gc is identified.',
                                       censoring='Maximum observed stress at the cap is not a resolved fracture peak; work through cap is not toughness.',
                                       stability='Only three selected fine-grid states checked. Marginal means no resolved negative mode at that precision, not proof of stability; no claim of stability along the whole trajectory.',
                                       strict_tier='Both resolutions complete, calibration/force/energy gates pass, maximum stress and cap-work step differences<=5%, and all three fine selected states positive.',
                                       conditional_tier='Same gates, permitting marginal selected-state classifications; remains an explicitly conditional result, not a stability proof.',
                                       fracture_tier='Additionally requires resolved uncensored peaks at both resolutions and <=5% work-to-peak step difference.',
                                       statistics='Within-seed angle contrasts averaged first; primary group means require both prespecified planes for a seed. Four synthetic seeds; no biological p-values or independent-angle confidence intervals.',
                                       damage_precision='No damage-fraction precision tolerance was prespecified. Generic numerical qualification is not a damage-precision gate; damage-ranking aggregates require direction agreement at both resolutions.',
                                       scientific_validation=False))
    outdir.mkdir(parents=True, exist_ok=True)
    dump(outdir/'summary.json', summary)
    dump(outdir/'report-data.json', dict(schema=1, summary=summary, runs=list(rows.values()),
                                       resolution_pairs=list(resolution.values()), placement_pairs=placed,
                                       baseline_pairs=baselines, stiffness=stiff, curves=curves))
    dump(outdir/'input-hashes.json', dict(final_result_files=hashes,
                                        calibration_sha256=hashlib.sha256(calibration_path.read_bytes()).hexdigest(),
                                        stiffness_sha256=hashlib.sha256(stiffness_path.read_bytes()).hexdigest() if stiffness_path.exists() else None))
    csvout(outdir/'runs.csv', list(rows.values())); csvout(outdir/'resolution-pairs.csv', list(resolution.values()))
    csvout(outdir/'placement-pairs.csv', placed); csvout(outdir/'baseline-pairs.csv', baselines)
    csvout(outdir/'stiffness-pairs.csv', stiff['paired'])
    return summary


def self_test():
    assert len(expected_keys()) == 160
    assert sign_agreement(.01,-.01)[0] is False
    assert sign_agreement(0,.01)[0] is False
    assert sign_agreement(0,0)==(True,'both_zero_no_rank_difference')
    assert sign_agreement(.01,.02)[0] is True
    assert key_of({}, f's{RESOLUTIONS[1]}-seed29-p1-t0.2-clustered-0.15.error.json') == (29,1,.2,'clustered',.15,RESOLUTIONS[1])
    def record(kind=STRICT_STABILITY, cap_peak=False):
        n=RESOLUTIONS[1]
        frames=[dict(gamma=.5*i/n,accepted=True,residual=1e-9,work=i/n,energy=.6*i/n,removedEnergy=.3*i/n,relaxEnergy=.1*i/n,damage=.2*i/n) for i in range(n+1)]
        return dict(status='converged',trajectoryComplete=True,peakResolved=not cap_peak,peakRightCensored=cap_peak,
                    terminalRelativeEnergyError=0,peakStress=2,peakGamma=.5 if cap_peak else .3,
                    workThroughCap=1,workThroughLastAccepted=1,workToPeak=None if cap_peak else .7,frames=frames,
                    selected_state_stability=[dict(label=l,classification=kind,max_free_gradient=1e-9) for l in sorted(EXPECTED_LABELS)])
    cal={29:dict(scale_Pa=10,accepted=True)};key=(29,1,.2,'clustered',.15,RESOLUTIONS[1])
    fine,_=audit_record(record(),key,cal);coarse=dict(fine,steps=RESOLUTIONS[0])
    pair=resolution_pair(key[:-1],coarse,fine)
    assert pair['numerical_qualified_strict'] and pair['fracture_endpoint_qualified_strict']
    marginal,_=audit_record(record(MARGINAL_STABILITY),key,cal)
    p=resolution_pair(key[:-1],coarse,marginal)
    assert p['numerical_qualified_conditional'] and not p['numerical_qualified_strict']
    for kind in ('negative_curvature_confirmed','unresolved_finite_difference_accuracy','unresolved_negative_mode'):
        bad,_=audit_record(record(kind),key,cal)
        assert not resolution_pair(key[:-1],coarse,bad)['numerical_qualified_conditional']
    censored,_=audit_record(record(cap_peak=True),key,cal)
    p=resolution_pair(key[:-1],censored,censored)
    assert p['numerical_qualified_strict'] and not p['fracture_endpoint_qualified_strict']
    broken=record();broken['terminalRelativeEnergyError']=.03
    bad,_=audit_record(broken,key,cal);assert not bad['energy_gate']
    p=resolution_pair(key[:-1],dict(coarse,maximum_observed_stress_model=2.2),fine)
    assert not p['step_maximum_stress_gate'] and not p['numerical_qualified_strict']
    assert resolution_pair(key[:-1],None,fine)['qualification']=='missing_resolution'
    pairs=[dict(seed=29,plane=1,density=.15,metric='test',difference=1,ratio=2,qualified_strict=True)]
    agg=seed_aggregate(pairs,('density','metric'),'qualified_strict')[0]
    assert agg['seeds_with_both_angles']==0 and agg['mean_of_seed_mean_differences'] is None
    print('PASS: expected counts, filename keys, energy/step/stability/censoring gates, and seed-angle aggregation.')


def main():
    global RESOLUTIONS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'remote-completed'/'results')
    parser.add_argument('--out',type=Path,default=ROOT/'analysis')
    parser.add_argument('--calibration',type=Path,default=ROOT/'amplitude-calibration-final.json')
    parser.add_argument('--stiffness',type=Path,default=ROOT/'stiffness.json')
    parser.add_argument('--coarse-steps',type=int,default=25,help='Primary coarse resolution (default25); use100 for preserved controls.')
    parser.add_argument('--fine-steps',type=int,default=50,help='Primary fine resolution and selected-state stability audit resolution (default50); use200 for preserved controls.')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.coarse_steps <= 0 or args.fine_steps <= args.coarse_steps:
        parser.error('Require0 < coarse-steps < fine-steps.')
    RESOLUTIONS=(args.coarse_steps,args.fine_steps)
    if args.self_test:
        self_test();return
    try:
        summary=analyze(args.input,args.out,args.calibration,args.stiffness)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary['counts'],indent=2))
    print('Outputs:',args.out)


if __name__=='__main__':
    main()
