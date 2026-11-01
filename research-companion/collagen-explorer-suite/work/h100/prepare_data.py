"""Read saved study data only; no imported research code or simulations run."""
from pathlib import Path
import csv, json, math, hashlib, statistics, shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/path/to/Codex/2026-10-31/referenced-chatgpt-conversation-this-is-an-4/outputs/collagen-matched-stiffness')
DEST = ROOT / 'work/site/dist/h100'
BATCHES = {'lbfgs-hold': 576, 'lbfgs-large': 2304}
METRICS = ['stress_retention', 'initial_RMS_strain']

def read(name):
    with (SOURCE / 'results' / name).open() as f:
        return list(csv.DictReader(f))

contrasts = [r for r in read('paired-contrasts.csv') if r['batch'] in BATCHES and float(r['kind']) == 0 and r['metric'] in METRICS]
cases = [r for r in read('case-summary.csv') if r['batch'] in BATCHES and float(r['kind']) == 0]
records = []
for c in contrasts:
    rows = [r for r in cases if all(r[k] == c[k] for k in ['batch', 'L', 'kappa', 'r', 'beta', 'kind', 'threshold'])]
    pairs = {}
    flag = 'initial_state_converged' if c['metric'].startswith('initial_') else 'converged'
    for r in rows:
        seed = int(float(r['seed']))
        arch = 'uniform' if float(r['architecture']) == 0 else 'clustered'
        value = float(r[c['metric']]) if r[c['metric']] else None
        pairs.setdefault(seed, {'seed': seed})[arch] = {'value': value, 'valid': r[flag] == 'True' and value is not None and math.isfinite(value)}
    points = []
    for seed,p in sorted(pairs.items()):
        p['included'] = all(p.get(a, {}).get('valid') for a in ['uniform', 'clustered'])
        points.append(p)
    good = [p for p in points if p['included']]
    assert len(good) == int(c['valid_pairs'])
    for arch in ['uniform', 'clustered']:
        assert math.isclose(statistics.mean(p[arch]['value'] for p in good), float(c[arch+'_mean']), abs_tol=1e-12)
    assert math.isclose(statistics.mean(p['clustered']['value']-p['uniform']['value'] for p in good), float(c['paired_mean_difference']), abs_tol=1e-12)
    record = {k: float(c[k]) for k in ['kappa','r','beta','uniform_mean','clustered_mean','paired_mean_difference','bootstrap_low','bootstrap_high']}
    record.update(nodes=BATCHES[c['batch']], batch=c['batch'], metric=c['metric'], valid_pairs=int(c['valid_pairs']), attempted_pairs=int(c['attempted_pairs']), pairs=points)
    records.append(record)

data = {'schema': 1, 'records': records, 'source': 'Published summary workbook, Paired contrasts and Case summaries sheets; matching archived CSV files', 'interval': 'Pointwise 95% paired seed bootstrap, 2,000 resamples; no multiplicity correction or biological uncertainty'}
assert len(records) == 32
(DEST/'results.json').write_text(json.dumps(data, separators=(',',':')))
for name in ['paired-contrasts.csv','case-summary.csv']:
    selected = contrasts if name.startswith('paired') else cases
    with (DEST/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)

# Saved topology, not a regenerated stochastic graph. Show original coordinates
# and retained edge masks. Periodic edges crossing the display cell are omitted.
for batch, nodes in BATCHES.items():
    fields=read(batch+'/example-fields.csv')
    for arch,label,color in [(0,'uniform','#85d5c2'),(1,'clustered','#f3a467')]:
        rows=[r for r in fields if int(r['architecture'])==arch and int(r['seed'])==0]
        assert len(rows)==nodes
        L=math.isqrt(nodes);coord={int(r['node']):(float(r['x']),float(r['y'])) for r in rows}
        xmax=max(x for x,y in coord.values());ymax=max(y for x,y in coord.values());scale=min(480/xmax,275/ymax)
        sx=lambda x: 20+x*scale
        sy=lambda y: 300-y*scale
        lines=[];retained=0
        for r in rows:
            i=int(r['node']);x,y=coord[i];ix,iy=i%L,i//L
            for direction in range(3):
                if int(r['edge'+str(direction)])!=1:continue
                retained+=1
                jx,jy=[(ix+1,iy),(ix,iy+1),(ix-1,iy+1)][direction]
                if not (0<=jx<L and 0<=jy<L):continue
                xx,yy=coord[jy*L+jx]
                lines.append(f'<path d="M{sx(x):.2f},{sy(y):.2f} L{sx(xx):.2f},{sy(yy):.2f}"/>')
        assert retained==int(1.8*nodes)
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 320" role="img" aria-label="Saved seed zero {label} network topology, {nodes} nodes"><title>Saved {label} topology: {nodes} nodes, {retained} retained edges</title><g fill="none" stroke="{color}" stroke-width="1.15" opacity=".85">'+''.join(lines)+'</g></svg>'
        (DEST/f'network-{nodes}-{label}.svg').write_text(svg)

manifest={str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'results/paired-contrasts.csv',SOURCE/'results/case-summary.csv',SOURCE/'collagen-matched-stiffness-summary.xlsx']}
(DEST/'source-checksums.json').write_text(json.dumps(manifest,indent=2))
shutil.copyfile(ROOT/'outputs/interactive_explorer.html',ROOT/'work/site/dist/original.html')
print(json.dumps({'comparisons':len(records),'hold_cases':len(cases),'all_paired_means_verified':True,'original_preserved':True}))
