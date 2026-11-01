import json,math,statistics,sys,struct,zlib,html
from pathlib import Path
from collections import defaultdict
base=Path(__file__).resolve().parent.parent;out=Path(json.loads((base/'active-run.json').read_text())['path']);vis=base/'visualizations'
rows=json.loads((out/'summary.json').read_text());families=['triangular2d','fcc3d','disordered3d'];colors=['#63d8ba','#edb665','#aa9fef'];groups=[];numerics=[]
for family in families:
 for mode in ['tension','shear']:
  for pattern in ['intact','clustered','distributed']:
   rs=[r for r in rows if r['family']==family and r['loading']==mode and r['pattern']==pattern and r['refinement']=='refined' and r['normalization']=='matched_tension_K'];valid=[r for r in rs if r['status']=='completed'];vals=[r['work'] for r in valid]
   rng=__import__('random').Random(778);means=sorted(statistics.mean(rng.choices(vals,k=len(vals))) for _ in range(2000)) if vals else []
   groups.append({'family':family,'loading':mode,'pattern':pattern,'valid':len(valid),'total':len(rs),'censored':sum(r['censored'] for r in valid),'mean_work':statistics.mean(vals) if vals else None,'mean_ci95_bootstrap':[means[49],means[1949]] if vals else None,'mean_failure_strain':statistics.mean(r['failure_strain'] for r in valid if not r['censored']) if any(not r['censored'] for r in valid) else None})
lookup={r['case_id']:r for r in rows}
for r in rows:
 if r['normalization']=='matched_tension_K' and r['refinement']=='base':
  f=lookup[r['case_id'].replace('-base-','-refined-')]
  if r['status']==f['status']=='completed':numerics.append({'base_case':r['case_id'],'work_relative_difference':abs(r['work']-f['work'])/max(abs(f['work']),1e-15),'failure_strain_difference':None if r['failure_strain'] is None or f['failure_strain'] is None else abs(r['failure_strain']-f['failure_strain']),'censoring_changed':r['censored']!=f['censored']})
paired=[]
for family in families:
 for mode in ['tension','shear']:
  for pat in ['clustered','distributed']:
   vs=[]
   for seed in range(101,111):
    r=lookup[f'{family}-{seed}-{pat}-{mode}-refined-matched_tension_K'];i=lookup[f'{family}-{seed}-intact-{mode}-refined-matched_tension_K']
    if r['status']==i['status']=='completed':vs.append(r['work']/i['work']-1)
   paired.append({'family':family,'loading':mode,'pattern':pat,'n':len(vs),'mean_paired_work_fraction_change':statistics.mean(vs) if vs else None,'seed_effects':vs})
analysis={'groups':groups,'paired_damage_effects':paired,'refinement':{'pairs':len(numerics),'max_work_relative_difference':max(n['work_relative_difference'] for n in numerics),'median_work_relative_difference':statistics.median(n['work_relative_difference'] for n in numerics),'over_5percent':sum(n['work_relative_difference']>.05 for n in numerics),'censoring_changed':sum(n['censoring_changed'] for n in numerics),'details':numerics},'max_residual':max(r['max_residual'] for r in rows),'failed_reported_cases':sum(r['status']!='completed' for r in rows),'max_damage_energy_increase':max(r['energy_increase_on_damage'] or 0 for r in rows),'maximum_match_error':max(abs(r['intact_tension_K']-1) for r in rows if r['normalization']=='matched_tension_K')}
(base/'analysis.json').write_text(json.dumps(analysis,indent=2))
def esc(t):return html.escape(str(t))
def start(title,sub):return [f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="650"><rect width="100%" height="100%" fill="#101d2a"/><style>text{{font:16px Arial;fill:#eaf1f6}}.s{{font-size:13px;fill:#b6c4d1}}.t{{font-size:27px;font-weight:bold}}</style><text x="35" y="45" class="t">{esc(title)}</text><text x="35" y="75" class="s">{esc(sub)}</text>']
for mode in ['tension','shear']:
 s=start('Matched stiffness: '+mode+' work to operational failure','Mean ± bootstrap 95% interval over 10 seeds. Refined strain step 0.005. Units: work / intact axial K; length = 1.')
 mx=max(g['mean_ci95_bootstrap'][1] for g in groups if g['loading']==mode and g['mean_ci95_bootstrap'])*1.12
 for j,pat in enumerate(['intact','clustered','distributed']):
  y=150+j*140;s.append(f'<text x="35" y="{y}">{pat}</text>')
  for i,fam in enumerate(families):
   g=next(g for g in groups if g['family']==fam and g['loading']==mode and g['pattern']==pat);yy=y+10+i*27;mean=g['mean_work'];lo,hi=g['mean_ci95_bootstrap'];x=lambda v:280+650*v/mx
   s.append(f'<rect x="280" y="{yy}" width="{650*mean/mx}" height="18" fill="{colors[i]}"/><path d="M{x(lo)},{yy+9} H{x(hi)} M{x(lo)},{yy+3} V{yy+15} M{x(hi)},{yy+3} V{yy+15}" stroke="white"/><text x="960" y="{yy+14}" class="s">{mean:.5f}</text>')
 for i,fam in enumerate(families):s.append(f'<text x="{35+i*330}" y="585" style="fill:{colors[i]}">{fam}</text>')
 s.append('<text x="35" y="620" class="s">Synthetic central-force brittle networks; large-deformation geometry, buckling and collagen chemistry are absent.</text></svg>');(vis/f'network-work-{mode}.svg').write_text(''.join(s))
# Minimal palette rasterizer and standards-compliant fixed-code-width GIF stream.
PAL=[(16,29,42),(99,216,186),(237,182,101),(170,159,239),(95,67,79),(233,239,244),(62,80,95),(236,100,100)]+[(0,0,0)]*8
FONT={'0':['111','101','101','101','111'],'1':['010','110','010','010','111'],'2':['111','001','111','100','111'],'3':['111','001','111','001','111'],'4':['101','101','111','001','001'],'5':['111','100','111','001','111'],'6':['111','100','111','101','111'],'7':['111','001','010','010','010'],'8':['111','101','111','101','111'],'9':['111','101','111','001','111'],'D':['110','101','101','101','110'],'F':['111','100','110','100','100'],'C':['111','100','100','100','111'],'E':['111','100','110','100','111'],'P':['110','101','110','100','100'],'S':['111','100','111','001','111'],'.':['000','000','000','000','010'],'-':['000','000','111','000','000'],' ':['000']*5}
W,H=720,300
def label(p,x,y,t,c=5):
 for ch in t:
  for j,row in enumerate(FONT.get(ch,['000']*5)):
   for i,v in enumerate(row):
    if v=='1':
     for dx in range(2):
      for dy in range(2):
       xx=x+2*i+dx;yy=y+2*j+dy
       if 0<=xx<W and 0<=yy<H:p[yy*W+xx]=c
  x+=8

def line(p,x1,y1,x2,y2,c):
 n=max(1,int(max(abs(x2-x1),abs(y2-y1))));n=min(n,1000)
 for q in range(n+1):
  x=round(x1+(x2-x1)*q/n);y=round(y1+(y2-y1)*q/n)
  if 0<=x<W and 0<=y<H:p[y*W+x]=c

def gif(path,frames):
 data=bytearray(b'GIF89a'+struct.pack('<HHBBB',W,H,0xf3,0,0)+bytes(v for col in PAL for v in col)+b'!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
 for frame in frames:
  data+=b'!\xf9\x04\x04'+struct.pack('<H',14)+b'\x00\x00'+b','+struct.pack('<HHHHB',0,0,W,H,0)+b'\x04'
  packed=bytearray();buf=0;nb=0
  def emit(code):
   nonlocal buf,nb
   buf|=code<<nb;nb+=5
   while nb>=8:packed.append(buf&255);buf>>=8;nb-=8
  for i in range(0,len(frame),10):
   emit(16)
   for v in frame[i:i+10]:emit(v)
  emit(17)
  if nb:packed.append(buf&255)
  for i in range(0,len(packed),255):chunk=packed[i:i+255];data+=bytes([len(chunk)])+chunk
  data+=b'\x00'
 data+=b';';path.write_bytes(data)
def png(path,p):
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 raw=b''.join(b'\x00'+bytes(v for ind in p[y*W:(y+1)*W] for v in PAL[ind]) for y in range(H));path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
for mode in ['tension','shear']:
 for pat in ['intact','clustered','distributed']:
  gs=[json.loads((out/'geometry'/f'{f}-101.json').read_text()) for f in families];rs=[json.loads((out/'raw'/f'{f}-101-{pat}-{mode}-refined.json').read_text()) for f in families];frames=[]
  # Same prescribed strain index in every panel; panels freeze at their operational endpoint.
  for frame_index in range(0,49,2):
   p=bytearray(W*H)
   for i,(g,r) in enumerate(zip(gs,rs)):
    if not r['frames']:continue
    fr=r['frames'][min(frame_index,len(r['frames'])-1)];d=g['dimension'];active=set(fr['active']);pts=[]
    for j,pt in enumerate(g['points']):
     q=[pt[a]+fr['displacement'][j*d+a] for a in range(d)];x=q[0]+(.3*q[1] if d==3 else 0);y=q[-1]+(.12*q[1] if d==3 else 0);pts.append((i*240+20+x*145,255-y*150))
    for ei,e in enumerate(g['edges']):
     if ei not in active:line(p,*pts[e['a']],*pts[e['b']],4)
    for ei in fr['active']:
     e=g['edges'][ei];line(p,*pts[e['a']],*pts[e['b']],i+1)
    label(p,i*240+18,15,['2D','FCC','3D'][i],i+1);label(p,i*240+18,34,'EPS '+format(fr['strain'],'.3f'));label(p,i*240+18,275,'-'+str(len(g['edges'])-len(active)),7)
   frames.append(p)
  gif(vis/f'{mode}-{pat}.gif',frames);png(vis/f'{mode}-{pat}-still.png',frames[len(frames)//2])
print(json.dumps({k:v for k,v in analysis.items() if k not in ['groups','paired_damage_effects','refinement']},indent=2));print(json.dumps({'groups':groups,'refinement':{k:v for k,v in analysis['refinement'].items() if k!='details'}},indent=2))
