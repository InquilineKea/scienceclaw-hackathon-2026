"""Original stdlib report and explicitly requested bounded staging; no upload.

Run only after results, frozen selection and numerical controls are complete.
Default writes REPORT.md plus public-audit-summary.json locally. --stage copies
an allowlisted public source/audit export; it never commits, uploads or deletes.
Unknown gates fail closed. Never imports simulation or third-party packages.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
DEST = Path('/private/tmp/scienceclaw-final-media-publication/collagen-nonlinear-heldout')
GATES = ('equilibrium', 'finite_energy_history', 'nonnegative_dissipation', 'work_balance', 'kkt', 'positive_jacobian',
         'step_refinement', 'angular_refinement',
         'no_detected_negative_curvature', 'hvp_fd')
SOURCE_EXT = {'.mjs', '.cpp', '.py'}
AUDIT_EXT = {'.md', '.json', '.py', '.cpp', '.mjs'}
PUBLIC_FILES = {'README.md', 'REPORT.md', 'public-audit-summary.json', 'PROTOCOL-FROZEN.md',
                'PROTOCOL-DRAFT.md', 'NUMERICAL-AMENDMENT.md', 'FINAL-DESIGN-AUDIT.md', 'SELECTION.json',
                'results.json', 'numerical-controls.json'}


def read(path):
    return json.loads(path.read_text())


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def fmt(x):
    return f'{x:.6g}' if finite(x) else 'Unavailable'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(results, selection, controls):
    tests = results.get('test', [])
    bylabel = {r.get('label'): r for r in tests}
    harmonic = bylabel.get('Harmonic', {})
    combined = bylabel.get('combined', {})
    if not combined:
        combined = next((r for r in tests if str(r.get('label', '')).lower() == 'combined'), {})
    hm, cm = harmonic.get('metrics', {}), combined.get('metrics', {})
    h = hm.get('primary_equal_octant_vector_MSE_um2')
    c = cm.get('primary_equal_octant_vector_MSE_um2')
    improvement = 1-c/h if finite(c) and finite(h) and h > 0 else None
    def no_worse(a, b):
        return finite(a) and finite(b) and a <= b
    practical = dict(vector_mse_5percent=finite(improvement) and improvement >= .05,
        raw_strain_no_worse=no_worse(cm.get('strain_Frobenius_NRMSE'), hm.get('strain_Frobenius_NRMSE')),
        guarded_strain_no_worse=no_worse(combined.get('support', {}).get('strain_Frobenius_NRMSE'),
                                       harmonic.get('support', {}).get('strain_Frobenius_NRMSE')))
    def coverage(m):
        return ([x.get('nodes') for x in m.get('octants', [])], m.get('strain_tetrahedra'))
    practical['common_coverage'] = (len(cm.get('octants', [])) == 8 and coverage(cm) == coverage(hm)
        and finite(cm.get('strain_tetrahedra')) and cm['strain_tetrahedra'] > 0
        and combined.get('support', {}).get('centers') == harmonic.get('support', {}).get('centers')
        and finite(combined.get('support', {}).get('centers'))
        and combined['support']['centers'] > 0)
    supplied = controls.get('gates', {})
    gates = {k: supplied.get(k) is True for k in GATES}
    unknown = [k for k in GATES if not isinstance(supplied.get(k), bool)]
    row = next((r for r in results.get('rows', []) if r.get('name') == 'combined'), {})
    complete = row.get('valid') is True and bool(combined)
    selected = selection.get('selected', {}).get('combined')
    selected_present = isinstance(selected, dict) and bool(selected)
    matching = selected_present and all(finite(row.get(k)) and row.get(k) == selected.get(k) for k in ('b', 'y'))
    numerical = all(gates.values()) and not unknown
    qualified_win = complete and matching and numerical and all(practical.values())
    if qualified_win:
        conclusion = 'The selected combined surrogate passes the frozen practical and numerical criteria on the adaptively reused conditional benchmark.'
    elif not complete:
        conclusion = 'The selected combined surrogate has no complete converged final benchmark result; no qualified improvement is established.'
    elif not matching:
        conclusion = 'Final combined parameters could not be matched to the frozen selection; no qualified comparison is established.'
    elif not numerical:
        conclusion = 'Numerical qualification is failed or incomplete; descriptive errors do not establish a qualified improvement.'
    else:
        conclusion = 'The selected combined surrogate does not satisfy the full frozen practical improvement criterion on the reused benchmark.'
    return dict(scope='Adaptively reused measured-boundary-conditioned Pos008 benchmark; not a fresh confirmatory holdout',
                combined_complete=complete, frozen_selection_parameters_match=matching,
                vector_mse_fractional_improvement=improvement,
                practical_gates=practical, numerical_gates=gates,
                unknown_numerical_gates=unknown, numerical_qualified=numerical,
                qualified_practical_win=qualified_win, conclusion=conclusion,
                independent_biological_validation=False, tests=tests)


def report(summary, selection, controls):
    lines = ['# Nonlinear collagen surrogate versus harmonic interpolation', '',
        summary['conclusion'], '',
        'Pos008 was inspected in the preceding study and is an adaptively reused benchmark. '
        'Pos007 selects parameters; Pos004 supplies numerical commissioning. '
        'All results are conditional on measured inner/outer boundary motion. '
        'This is not an independent biological validation or known-force experiment.', '',
        '## Final field comparison', '',
        '| Model | Equal-octant vector MSE (µm²) | Equal-octant RMSE (µm) | Raw P1 strain NRMSE | Guarded local-strain NRMSE |',
        '|---|---:|---:|---:|---:|']
    for r in summary['tests']:
        m = r.get('metrics', {})
        label = str(r.get('label', 'Unknown')).replace('|', '/')
        lines.append('| '+label+' | '+' | '.join(fmt(v) for v in (
            m.get('primary_equal_octant_vector_MSE_um2'), m.get('balanced_vector_RMSE_um'),
            m.get('strain_Frobenius_NRMSE'), r.get('support', {}).get('strain_Frobenius_NRMSE')))+' |')
    improvement = summary['vector_mse_fractional_improvement']
    lines += ['', 'Combined-model vector MSE improvement relative to harmonic: '+
              (fmt(100*improvement)+'%' if finite(improvement) else 'unavailable')+'.', '',
        'Displacement errors weight the eight spatial octants equally. Raw P1 strain uses '
        'volume-weighted infinitesimal tensor Frobenius error; guarded 5×5×5 strain uses '
        'equal eligible local affine-fit centers. These are different correlated outcomes, '
        'not independent replications. Secondary NRMSE is observed-field normalized after '
        'supplied-boundary-only translation removal. Lead with physical displacement errors.', '',
        '## Qualification', '', '| Required gate | Pass |', '|---|---|']
    for kind in ('practical_gates', 'numerical_gates'):
        for k, v in summary[kind].items():
            label = 'unknown' if k in summary['unknown_numerical_gates'] else 'yes' if v else 'no'
            lines.append(f'| {k} | {label} |')
    lines += ['', 'Practical success requires at least 5% lower vector MSE than unchanged harmonic '
        'and neither raw nor guarded strain error worse, with complete common coverage. '
        'Numerical qualification additionally requires every listed boolean gate explicitly true; '
        'missing gates fail closed. Step and angular refinements must be assessed separately '
        'against the 110-direction/10-step primary case. A nonnegative finite Lanczos subspace '
        'screen does not prove stability, uniqueness or absence of every negative mode.', '',
        'Thresholds, detailed controls and retained failures: [numerical-controls.json](numerical-controls.json). '
        'Full frozen selection and candidate outcomes: [SELECTION.json](SELECTION.json). '
        'Descriptive final results: [results.json](results.json).', '',
        '## Interpretation limits', '',
        'Selected parameters are predictive candidates, not measured buckling or sliding properties. The twelve-arm directional continuum varies compression softening and irreversible '
        'plastic lengthening with fixed tensile priors. Its slip state is an internal surrogate, '
        'not observed junction sliding or molecular damage. Proportional loading from a '
        'drug-relaxed reference is assumed, not an observed time history or established virgin state. '
        'No actual collagen graph connectivity is reconstructed. Missing boundary measurements '
        'receive modeled natural conditions. Uniform absolute stiffness is not identified by '
        'these homogeneous displacement-controlled fields. No aging, cell-force, fracture, '
        'toughness or species claim follows.', '',
        'The same few positions and thousands of correlated vectors/tetrahedra are not '
        'independent biological replicates. Unknown specimen/batch independence and uncalibrated '
        'DVC, reference-registration and segmentation uncertainty prevent an experimental '
        'adequacy claim from numerical residuals alone. Better benchmark error would require '
        'confirmation on genuinely uninspected public fields with a new frozen contract.', '',
        '## Source and provenance', '',
        '- [Frozen protocol](PROTOCOL-FROZEN.md) and [design audit](FINAL-DESIGN-AUDIT.md).',
        '- [Prior measured-field source snapshot](../collagen-measured-3d-validation/) retains '
        'mask/provenance records and baseline methodology.',
        '- [Saenopy primary study](https://doi.org/10.1038/s41567-024-02632-8) '
        'and [public example release](https://github.com/rgerum/saenopy/releases/tag/v0.7.4).',
        '- Lebedev angular tables are referenced in the frozen protocol; raw tables are '
        'excluded from this bounded export.', '',
        'The public package retains original source and bounded audit/result records. '
        'Raw images, input fields, binary executables/states, probes and downloaded '
        'third-party tables are excluded. This report does not claim those exclusions '
        'are a complete reproducibility archive; original local research archives retain them.']
    return '\n'.join(lines)+'\n'


def stage(root, dest):
    candidates = []
    for f in root.iterdir():
        if f.is_file() and (f.name in PUBLIC_FILES or f.suffix in SOURCE_EXT):
            candidates.append(f)
    audit = root/'audit'
    if audit.exists():
        candidates += [f for f in audit.iterdir() if f.is_file() and f.suffix in AUDIT_EXT
                       and not any(w in f.name.lower() for w in ('probe', 'lebedev', 'raw', 'input'))]
    if any(f.is_symlink() for f in candidates):
        raise ValueError('Refusing symlink in public allowlist')
    total = sum(f.stat().st_size for f in candidates)
    if total > 30_000_000 or any(f.stat().st_size > 10_000_000 for f in candidates):
        raise ValueError('Bounded source/audit export exceeds size limit; inspect explicitly')
    dest.mkdir(parents=True, exist_ok=True)
    # Fresh/empty destination avoids stale excluded files surviving an earlier export.
    if any(dest.iterdir()):
        raise ValueError('Staging destination must be empty; no deletion is performed')
    manifest = []
    for source in sorted(candidates):
        relative = source.relative_to(root)
        target = dest/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = sha(source)
        if sha(target) != digest:
            raise ValueError('Staged hash mismatch: '+str(relative))
        manifest.append(dict(file=str(relative), bytes=source.stat().st_size, sha256=digest))
    (dest/'PUBLIC-MANIFEST.json').write_text(json.dumps(dict(
        scope='Bounded source/audit export; no upload performed', bytes=total, files=manifest,
        exclusions=['binaries', 'inputs', 'raw image/archive files', 'fields.json',
                    'Lebedev raw tables', 'probes', 'run/test binary states']), indent=2)+'\n')
    print('Staged', len(manifest), 'files and', total, 'bytes to', dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--stage', action='store_true')
    parser.add_argument('--dest', type=Path, default=DEST)
    args = parser.parse_args()
    root = args.root.resolve()
    result = read(root/'results.json'); selection = read(root/'SELECTION.json')
    controls = read(root/'numerical-controls.json')
    summary = derive(result, selection, controls)
    summary['input_sha256'] = {n: sha(root/n) for n in (
        'results.json', 'SELECTION.json', 'numerical-controls.json', 'PROTOCOL-FROZEN.md')}
    (root/'REPORT.md').write_text(report(summary, selection, controls))
    (root/'public-audit-summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    print(summary['conclusion'])
    if args.stage:
        stage(root, args.dest)


if __name__ == '__main__':
    main()
