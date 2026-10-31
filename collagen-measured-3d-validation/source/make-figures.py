"""Original standard-library SVG scientific plots from frozen outcomes."""
from pathlib import Path
import json,html,math
P=Path(__file__).parent
COL={'Batch A':'#7254a3','Batch B':'#23858b','Batch C':'#172b42','model':'#cf6b26','linear':'#888f99'}
def begin(W,H):return[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#f7f9fc"/>']
def text(S,x,y,t,size=17,color='#172b42',anchor='start'):S.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(str(t))}</text>')
def axes(S,L,T,W,H,xmax,ymax,xlabel,ylabel):
 X=lambda x:L+x*W/xmax;Y=lambda y:T+H-y*H/ymax
 for i in range(5):
  x=xmax*i/4;y=ymax*i/4;S.append(f'<path d="M{L},{Y(y)}H{L+W}" stroke="#dce4ed"/>');text(S,L-10,Y(y)+5,f'{y:.2g}',14,anchor='end');text(S,X(x),T+H+24,f'{x:.2g}',14,anchor='middle')
 text(S,L+W/2,T+H+54,xlabel,17,anchor='middle');text(S,L,T-13,ylabel);return X,Y
def poly(S,pts,color,dash=''):
 S.append('<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="2.5" stroke-dasharray="{dash}"/>')
b=json.loads((P/'bulk-results.json').read_text());S=begin(1240,760);text(S,30,40,'Measured collagen: held-out batch prediction',30);text(S,30,76,'Fit batch A → select on B → test C · 1.2 mg/mL primary · fixed model, no C rescaling',19)
curves=[c for c in b['curves'] if c['concentration']==1.2];ym=max(r['y'] for c in curves for r in c['observations'])*1.12;X,Y=axes(S,75,150,530,350,.19,ym,'Shear strain γ','Shear stress (Pa), 1.2 mg/mL')
for c in curves:poly(S,[(X(r['x']),Y(r['y'])) for r in c['observations']],COL[c['batch']])
poly(S,[(X(r['x']),Y(y)) for r,y in zip(curves[0]['observations'],curves[0]['prediction'])],COL['model'],'7 5')
for j,(label,color) in enumerate([('A: fit',COL['Batch A']),('B: selection',COL['Batch B']),('C: final test',COL['Batch C']),('Frozen prediction',COL['model'])]):text(S,80+(j%2)*265,580+(j//2)*27,label,17,color)
text(S,720,137,'Final-test stress NRMSE',21)
for j,c in enumerate([.6,1.2,2.4]):
 x=735+j*155;v=b['test'][str(c)]['NRMSE'];v0=b['linear_test'][str(c)]['NRMSE']
 for xx,val,color in [(x,v0,COL['linear']),(x+44,v,COL['model'])]:S.append(f'<rect x="{xx}" y="{500-320*val}" width="35" height="{320*val}" fill="{color}"/>');text(S,xx+17,488-320*val,f'{val:.3f}',15,anchor='middle')
 text(S,x+40,528,f'{c} mg/mL',16,anchor='middle')
text(S,720,568,'Gray: linear · Orange: selected fiber law',17);text(S,720,595,'NRMSE = RMSE / RMS measured stress',15)
text(S,30,653,'The test batch is substantially underpredicted; nonlinear fitting gives only a small improvement over linear elasticity.',18)
text(S,30,686,'Published batch-average ramp curves; not raw replicate histories, oscillatory G′/G″, or matched 3D architecture tests.',17)
text(S,30,722,'Source: Böhringer et al., Nature Physics (2024), Extended Data Fig. 2 source data. Common strain domain 0.005–0.19.',16)
S.append('</svg>');(P/'bulk-validation.svg').write_text('\n'.join(S))
r=json.loads((P/'Pos008-results.json').read_text());S=begin(1240,780);text(S,30,42,'Measured 3D collagen: withheld interior field, position 008',29);text(S,30,78,'Boundary-conditioned prediction · 4,355 valid score vectors · one held-out position, not 4,355 replicates',18)
names=['zero','affine_boundary_fit','harmonic_interpolation','elastic_nu_0'];labels=['Zero','Affine','Harmonic','Elastic ν=0'];colors=['#a6b0ba','#7691ae','#22878d','#bf762d']
for j,(metric,title,maxv) in enumerate([('balanced_vector_RMSE_um','Displacement RMSE (µm), equal octant weight',3.5),('strain_Frobenius_NRMSE','Raw P1 strain relative error, volume weighted',1.1)]):
 X,Y=axes(S,85+j*610,155,500,300,4,maxv,'Predictor',title)
 for i,(n,l,col) in enumerate(zip(names,labels,colors)):
  q=next(x for x in r['results'] if x['name']==n);v=q['metrics'][metric];x=95+j*610+i*125;S.append(f'<rect x="{x}" y="{Y(v)}" width="75" height="{455-Y(v)}" fill="{col}"/>');text(S,x+38,Y(v)-10,f'{v:.3f}',17,anchor='middle');text(S,x+38,485,l,16,anchor='middle')
text(S,30,557,'Harmonic interpolation beats the selected isotropic elastic baseline. Displacement input is supplied only at known nodes.',18)
text(S,30,592,'No inverse-model cell forces are used as targets. Absolute stiffness cancels from the homogeneous Dirichlet operator.',17)
text(S,30,627,'Raw P1 strains amplify image-correlation noise. Post-test 61×61×59 µm averaging retains 303 complete guarded stencils:',17)
d=json.loads((P/'strain-support-diagnostic.json').read_text())['records'][0]['metrics'];text(S,30,660,f"averaged strain NRMSE: harmonic {d['harmonic_interpolation']['strain_Frobenius_NRMSE']:.3f}; elastic {d['elastic_nu_0']['strain_Frobenius_NRMSE']:.3f}. No model reselection.",17)
text(S,30,704,'This is an internal measured-field test on a PIV sampling mesh; measured fiber connectivity and matched specimen rheology remain missing.',16)
text(S,30,745,'Source: public Saenopy ClassicSingleCellTFM v0.7.4 images/PIV fields, linked to Böhringer et al. (2024).',16);S.append('</svg>');(P/'spatial-validation.svg').write_text('\n'.join(S))
for name in ['bulk-validation','spatial-validation']:(P/(name+'-figure.html')).write_text('<html><style>body{margin:0;background:#f7f9fc}img{display:block;width:1240px}</style><img src="'+name+'.svg"></html>')
print('Wrote two scientific SVGs')
