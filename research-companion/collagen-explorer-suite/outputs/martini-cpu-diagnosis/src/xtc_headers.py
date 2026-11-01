"""Original XDR header-only reader; never decodes or executes trajectory payloads."""
import struct,json,math
from pathlib import Path
p=Path('outputs/martini-fibril-study/recovery-20261031/codex-martini3-20261031-01a18fb8/production-preconditioned-v002-45ns/div_CG/pilot45.xtc');frames=[]
with p.open('rb') as f:
 while True:
  offset=f.tell();b=f.read(52)
  if not b:break
  assert len(b)==52
  magic,n,step,t,*box=struct.unpack('>iiif9f',b);assert magic==1995
  size=struct.unpack('>i',f.read(4))[0];assert size==n
  if n<=9:f.seek(n*12,1)
  else:
   meta=f.read(36);assert len(meta)==36
   precision,*rest=struct.unpack('>f8i',meta);count=rest[-1];assert 0<count<100000000;f.seek((count+3)//4*4,1)
  vol=box[0]*(box[4]*box[8]-box[5]*box[7])-box[1]*(box[3]*box[8]-box[5]*box[6])+box[2]*(box[3]*box[7]-box[4]*box[6]);frames.append({'step':step,'time_ps':t,'box_nm':box,'volume_nm3':vol})
Path('outputs/martini-cpu-diagnosis/trajectory-boxes.json').write_text(json.dumps(frames,indent=2)+'\n');print(json.dumps({'frames':len(frames),'first':frames[0],'last':frames[-1],'volume_ratio':frames[-1]['volume_nm3']/frames[0]['volume_nm3']},indent=2))
