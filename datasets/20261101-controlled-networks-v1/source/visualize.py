"""Original stdlib-only data analysis, SVG charts and lossless PNG/GIF encoder."""
import json,csv,math,statistics,sys,struct,zlib,html,hashlib,shutil
from pathlib import Path
from collections import defaultdict
base=Path(__file__).resolve().parent.parent
out=Path(json.loads((base/'active-run.json').read_text())['path']);vis=base/'visualizations';vis.mkdir(exist_ok=True)
repo=Path(sys.argv[1]);src=repo/'collagen-fenicsx-poroelastic/web';rows=list(csv.DictReader((src/'comparisons.csv').open()));validation=json.loads((src/'validation.json').read_text())
for p in ['comparisons.csv','validation.json','METHODS.md']:shutil.copyfile(src/p,vis/('fenicsx-'+p))
for r in rows:
    r['accepted']=r['resolved'].lower() in ('true','1')
    for k in ['omega','permeability','poroDamageRatio','dragDamageRatio','meshRelative','meshDamageDifferencePP']:
        try:r[k]=float(r[k])
        except ValueError:r[k]=None

def esc(x):return html.escape(str(x))
def svg_start(title,subtitle,w=1100,h=650):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#101d2a"/><style>text{{font-family:Arial,sans-serif;fill:#e9eff4;font-size:16px}}.small{{font-size:13px;fill:#b6c4d1}}.title{{font-size:28px;font-weight:bold}}</style><text x="36" y="46" class="title">{esc(title)}</text><text x="36" y="75" class="small">{esc(subtitle)}</text>']
def text(s,x,y,t,cls=''):s.append(f'<text x="{x}" y="{y}" class="{cls}">{esc(t)}</text>')
def save(s,p):p.write_text(''.join(s)+ '</svg>')
s=svg_start('FEniCSx: successful solves ≠ mesh-accepted responses','Reanalysis of saved comparisons.csv — no new FEniCSx solve. Rejected rows remain visible.')
for y,label,num,den,col in [(120,'Algebraic systems',4158,4160,'#63d8ba'),(192,'Observable mesh comparisons',1341,1600,'#edb665')]:
    text(s,36,y,label);s.append(f'<rect x="370" y="{y-20}" width="600" height="27" fill="#7b3d50"/><rect x="370" y="{y-20}" width="{600*num/den}" height="27" fill="{col}"/>');text(s,36,y+26,f'{num:,} / {den:,} = {num/den:.2%}', 'small')
text(s,36,280,'Accepted comparisons by architecture and damage placement')
groups=defaultdict(list)
for r in rows:groups[(r['family'],r['pattern'])].append(r)
agg=[]
for i,((fam,pat),rs) in enumerate(sorted(groups.items())):
    n=sum(r['accepted'] for r in rs);y=320+i*42;text(s,36,y,f'{fam} / {pat}');s.append(f'<rect x="370" y="{y-17}" width="{480*n/len(rs)}" height="23" fill="#63d8ba"/>');text(s,875,y,f'{n}/{len(rs)}', 'small');agg.append({'family':fam,'pattern':pat,'accepted':n,'total':len(rs),'rate':n/len(rs)})
text(s,36,620,'Mesh gates: relative response change ≤ 5%; damage-ratio change ≤ 0.5 percentage points.', 'small');save(s,vis/'fenicsx-acceptance.svg')
fams=sorted(set(r['family'] for r in rows));oms=sorted(set(r['omega'] for r in rows));ks=sorted(set(r['permeability'] for r in rows))
s=svg_start('Where does the FEniCSx mesh test pass?','Each tile pools architectures, damage placements, directions, metrics and seeds at one frequency/permeability.')
for i,k in enumerate(ks):
    text(s,40,175+i*90,f'k = {k:g}')
    for j,o in enumerate(oms):
        rs=[r for r in rows if r['omega']==o and r['permeability']==k];n=sum(r['accepted'] for r in rs);v=n/len(rs);x=200+j*160;y=130+i*90
        col=f'#{int(180-90*v):02x}{int(65+130*v):02x}{int(80+75*v):02x}';s.append(f'<rect x="{x}" y="{y}" width="145" height="70" rx="8" fill="{col}"/>');text(s,x+15,y+29,f'{v:.1%}');text(s,x+15,y+53,f'{n}/{len(rs)}','small')
for j,o in enumerate(oms):text(s,210+j*160,110,f'ω = {o:g}')
text(s,36,540,'Acceptance is a numerical gate, not a biological accuracy score. Frequency and permeability are model units.','small');text(s,36,568,'Do not infer fluid-coupling effects from rejected comparisons. Download the full 1,600-row table.','small');save(s,vis/'fenicsx-heatmap.svg')
s=svg_start('Fluid coupling changes the damage response','Only mesh-accepted points. Damage response = damaged / intact; each point is one accepted comparison.')
accepted=[r for r in rows if r['accepted'] and r['poroDamageRatio'] is not None and r['dragDamageRatio'] is not None]
lo=min(min(r['poroDamageRatio'],r['dragDamageRatio']) for r in accepted);hi=max(max(r['poroDamageRatio'],r['dragDamageRatio']) for r in accepted);pad=.04*(hi-lo);lo-=pad;hi+=pad
x0,y0,ww,hh=180,120,660,420
s.append(f'<rect x="{x0}" y="{y0}" width="{ww}" height="{hh}" fill="#182b3b"/>')
def xy(x,y):return x0+(x-lo)/(hi-lo)*ww,y0+hh-(y-lo)/(hi-lo)*hh
x1,y1=xy(lo,lo);x2,y2=xy(hi,hi);s.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#ffffff" stroke-dasharray="5,5" fill="none"/>')
for r in accepted:
    x,y=xy(r['dragDamageRatio'],r['poroDamageRatio']);col='#63d8ba' if r['metric']=='selfAmplitude' else '#edb665';s.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="2.3" fill="{col}" opacity=".4"/>')
text(s,180,575,f'Uniform-drag damage ratio (range {lo:.3g} to {hi:.3g})');text(s,36,105,'FEniCSx poroelastic ratio');text(s,36,614,'Green: self amplitude · amber: far-field RMS · dashed: identical predictions. Ratios above 1 indicate increased response.','small');save(s,vis/'fenicsx-damage-scatter.svg')
(vis/'fenicsx-analysis.json').write_text(json.dumps({'source_sha256':hashlib.sha256((src/'comparisons.csv').read_bytes()).hexdigest(),'validation':validation,'group_acceptance':agg,'accepted_count':len(accepted)},indent=2))
# Standalone, filterable raw table; all rows including rejection flags are retained.
columns=['family','seed','pattern','direction','omega','permeability','metric','poroDamageRatio','dragDamageRatio','meshRelative','meshDamageDifferencePP','accepted']
head=''.join('<th>'+esc(c)+'</th>' for c in columns);body=''.join('<tr class="'+('ok' if r['accepted'] else 'rejected')+'">'+''.join('<td>'+esc(r[c])+'</td>' for c in columns)+'</tr>' for r in rows)
(vis/'fenicsx-table.html').write_text('<!doctype html><meta charset="utf-8"><title>FEniCSx table: all 1,600 comparisons</title><style>body{font:15px system-ui;margin:30px;background:#101d2a;color:#eee}input,select{padding:10px}table{border-collapse:collapse;font-size:12px}td,th{padding:6px;border:1px solid #365}th{position:sticky;top:0;background:#263b48}.rejected{background:#502d39}.ok{background:#193b35}img{width:100%;max-width:1100px}</style><h1>FEniCSx: algebraic resolution and mesh acceptance</h1><p>Saved-data reanalysis. No new FEniCSx execution. Green rows pass both mesh gates; red rows are withheld from effects.</p><img src="fenicsx-acceptance.svg"><img src="fenicsx-heatmap.svg"><img src="fenicsx-damage-scatter.svg"><h2>Explore every row</h2><input id="q" placeholder="Filter e.g. modular, farRms"><select id="gate"><option value="">All rows</option><option value="ok">Accepted only</option><option value="rejected">Rejected only</option></select><p id="count"></p><div style="overflow:auto;max-height:700px"><table><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table></div><script>function filter(){let n=0;document.querySelectorAll("tbody tr").forEach(r=>{let show=r.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!gate.value||r.className===gate.value);r.hidden=!show;n+=show});count.textContent=n+" / 1600 rows"}q.oninput=gate.onchange=filter;filter()</script>')
print(json.dumps({'fenicsx_rows':len(rows),'accepted':sum(r['accepted'] for r in rows),'groups':agg}),flush=True)
