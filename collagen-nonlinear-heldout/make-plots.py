from pathlib import Path
import json,html
P=Path(__file__).parent
r=json.loads((P/'results.json').read_text());sel=json.loads((P/'SELECTION.json').read_text())
def start(title,sub):return ['<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="780" viewBox="0 0 1240 780"><rect width="1240" height="780" fill="#f7f9fc"/>',txt(30,45,title,30),txt(30,80,sub,18)]
def txt(x,y,t,size=16,color='#182c42'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}">{html.escape(str(t))}</text>'
S=start('Can nonlinear collagen mechanics beat interpolation?','Adaptively reused position 008 · frozen position007 selection · 4,355 guarded vectors · lower is better')
colors=['#22878d','#7c8795','#aa702b','#845da7','#bd544f']
for pane,(key,title,maxv) in enumerate([('balanced_vector_RMSE_um','Displacement RMSE (µm)',2.3),('strain_Frobenius_NRMSE','Raw P1 strain NRMSE',1.2)]):
 left=70+pane*610;S.append(txt(left,145,title,21))
 for k in range(5):
  v=maxv*k/4;y=460-v/maxv*270;S.append(f'<path d="M{left},{y}h500" stroke="#d8e1eb"/>');S.append(txt(left-35,y+4,f'{v:.2g}',14))
 for i,x in enumerate(r['test']):
  v=x['metrics'][key];xx=left+20+i*95;yy=460-v/maxv*270;S.append(f'<rect x="{xx}" y="{yy}" width="55" height="{460-yy}" fill="{colors[i%5]}"/>');S.append(txt(xx,yy-12,f'{v:.3f}',16));S.append(txt(xx-8,492,x['label'].capitalize(),13))
S.extend([txt(30,550,r['verdict'].split(' Numerical')[0],19),txt(30,579,'Numerical/practical qualification: '+('PASS' if r.get('qualified_practical_win') else 'pending or not established; see full controls'),17),txt(30,600,'Averaged local strain (303 guarded 5³ stencils):',19)])
for i,x in enumerate(r['test']):S.append(txt(35+i*240,635,f"{x['label']}: {x['support']['strain_Frobenius_NRMSE']:.3f}",17))
S.extend([txt(30,687,'One position; no independent-sample significance. Strain derives from PIV displacement, not an independent strain assay.'),txt(30,724,'Directional continuum + plastic lengthening surrogate; no measured fiber graph, absolute stiffness or fracture validation.'),'</svg>']);(P/'comparison.svg').write_text('\n'.join(S))
S=start('Parameter selection before the final comparison','Position007 · primary equal-octant vector MSE (µm²) · all twelve factorial arms, including failures')
S.append(txt(80,160,'Buckling scale / sliding yield',21));ys=[-1,.01,.04];bs=[-1,.0025,.01,.04]
for j,y in enumerate(ys):S.append(txt(420+j*220,160,'none' if y<0 else str(y),21))
for i,b in enumerate(bs):
 S.append(txt(100,240+i*85,'none' if b<0 else str(b),21))
 for j,y in enumerate(ys):
  q=next(x for x in sel['rows'] if x['b']==b and x['y']==y);v=q['metrics']['primary_equal_octant_vector_MSE_um2'] if q['valid'] else None;S.append(txt(420+j*220,240+i*85,f'{v:.5f}' if v is not None else 'FAILED',23))
S.append(txt(30,610,'Selected families: '+', '.join(f"{k} b={v['b'] if v['b']>=0 else 'none'}, y={v['y'] if v['y']>=0 else 'none'}" for k,v in sel['selected'].items() if k!='control'),17))
S.extend([txt(30,660,'Fixed: tensile onset0.04, exponential scale0.05, slip hardening0.05; 110 directions and10 load increments.',17),txt(30,700,'Sliding is irreversible surrogate lengthening; compression softens without an outcome-fitted stiffness floor.',17),txt(30,740,'See numerical control results for equilibrium, work balance, step/angular refinement and bounded curvature screen.',17),'</svg>']);(P/'selection.svg').write_text('\n'.join(S))
