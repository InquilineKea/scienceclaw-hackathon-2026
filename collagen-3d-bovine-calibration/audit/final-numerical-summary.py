"""Original stdlib summary writer. Explicit final analysis input is required.

Does not run a solver or infer completion from directory names. Partial inventory
is clearly labeled; four-seed comparator eligibility is kept separate from means
of the available eligible subset. No statistical significance is inferred.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raw = args.summary.read_bytes()
    s = json.loads(raw)
    c = s['counts']
    inventory_complete = (c['expected_final_cases'] == 160 and
                          c['final_cases_loaded'] == 160 and
                          c['missing_final_cases'] == 0 and
                          c['duplicate_case_keys'] == 0 and
                          c['unexpected_files'] == 0 and
                          c['complete_resolution_pairs'] == 80)
    result = dict(source_sha256=hashlib.sha256(raw).hexdigest(),
                  inventory_complete=inventory_complete,
                  scientific_validation=False, counts=c,
                  gates=s['gates'],
                  selected_state_classes=s['selected_state_stability_classification_counts'],
                  endpoint_counts=s['endpoint_counts_by_resolution'],
                  damage_resolution=s['damage_resolution_diagnostics'],
                  placement_comparisons=[], damage_comparisons=[])
    for source, dest in [('placement_aggregates', 'placement_comparisons'),
                         ('damage_ranking_aggregates', 'damage_comparisons')]:
        for r in s.get(source, []):
            tier = r['qualification_tier']
            complete_seeds = r['seeds_with_both_angles'] == 4
            qualified = tier != 'descriptive'
            result[dest].append(dict(
                **{k: r.get(k) for k in ('threshold', 'density', 'metric',
                    'qualification_tier', 'seeds_with_both_angles',
                    'paired_angle_records', 'mean_of_seed_mean_differences',
                    'seed_mean_difference_range', 'mean_of_seed_mean_ratios',
                    'seed_mean_ratio_range', 'seed_signs')},
                complete_four_seed_numerical_comparison=(inventory_complete and complete_seeds and qualified),
                subset_estimate=not complete_seeds,
                interpretation=('Descriptive output only' if not qualified else
                    'Complete four-seed qualified comparison; constitutive assumptions remain' if inventory_complete and complete_seeds else
                    'Qualified available subset only; no complete four-seed comparator claim')))
    result['limitations'] = [
        'Marginal selected-state classification is not a proof of stability.',
        'Checked states do not establish stability along the whole trajectory.',
        'Observed cap work is not toughness; unresolved and right-censored peaks remain distinct.',
        'Stress/work refinement gates do not establish damage-fraction precision.',
        'Four synthetic seeds; loading planes, thresholds and resolutions are repeated conditions.',
        'Bulk-matched Pa and J/m^3 scales are conditional; no Gc or measured architecture validation.']
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print('Final inventory complete:', inventory_complete)
    print('Saved numerical audit:', args.out)


if __name__ == '__main__':
    main()
