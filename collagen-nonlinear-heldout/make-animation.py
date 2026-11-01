"""Original static measured/predicted vector views with camera rotation, no invented dynamics."""
from pathlib import Path
import json,math,struct
from importlib.machinery import SourceFileLoader
P=Path(__file__).parent;R=SourceFileLoader('original_palette',str(P/'gif-helpers.py')).load_module();R.W=1260;R.H=520;W,H=R.W,R.H
f=json.loads((P/'fields.json').read_text());samples=[i for i,s in enumerate(f['score']) if s][::10];panels=[('OBSERVED PIV',None),('COMBINED','combined'),('HARMONIC','Harmonic')]
out=bytearray(b'GIF89a'+struct.pack('<HHBBB',W,H,0xf7,0,0)+bytes(v for rgb in R.PAL for v in rgb)+b'!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
for frame in range(32):
 buf=bytearray(W*H);ang=2*math.pi*frame/32+.4
 for pane,(title,name) in enumerate(panels):
  off=pane*420
  def proj(q):
   x,y,z=q;xx=math.cos(ang)*x-math.sin(ang)*y;yy=math.sin(ang)*x+math.cos(ang)*y
   return[off+210+.72*xx,270-.7*(.85*z+.45*yy)]
  R.text(buf,off+30,74,title,2)
  for i in range(8):
   for d in range(3):
    if not(i>>d&1):
     j=i|1<<d;a=[(1 if i>>k&1 else -1)*177 for k in range(3)];b=[(1 if j>>k&1 else -1)*177 for k in range(3)];R.line(buf,proj(a),proj(b),68)
  for q in f['cell_samples_um'][::3]:
   x,y=map(round,proj(q));R.pixel(buf,x,y,68)
  for i in samples:
   q=f['nodes'][i];u=f['targets'][i] if name is None else f['predictions'][name][i];mag=math.sqrt(sum(v*v for v in u));a=proj(q);b=proj([q[d]+8*u[d] for d in range(3)]);color=3+round(63*min(1,mag/8));R.line(buf,a,b,color,1);dx=b[0]-a[0];dy=b[1]-a[1];l=math.hypot(dx,dy)
   if l>2:
    for sg in [-1,1]:R.line(buf,b,[b[0]-3*dx/l+sg*2*dy/l,b[1]-3*dy/l-sg*2*dx/l],color)
 R.text(buf,25,16,'NONLINEAR COLLAGEN / REUSED POSITION 008',3);R.text(buf,25,445,'SAME GUARDED INTERIOR VECTORS / CELL MASK GRAY / COLOR IS DISPLACEMENT',2);R.text(buf,25,480,'ARROWS X8 / CAMERA ROTATION ONLY / ONE MEASURED IMAGE PAIR',2)
 out+=b'!\xf9\x04\x08'+struct.pack('<H',14)+b'\x00\x00'+b','+struct.pack('<HHHHB',0,0,W,H,0)+R.encode(buf)
out+=b';';(P/'nonlinear-prediction-3d.gif').write_bytes(out);print('GIF32frames',len(out),'bytes')
