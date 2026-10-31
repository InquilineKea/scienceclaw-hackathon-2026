"""Original stdlib TIFF/PNG reader and scientific projections; data never executed."""
from pathlib import Path
import struct,zipfile,zlib,binascii,re,json
P=Path(__file__).parent

def tiff(b):
 endian='<' if b[:2]==b'II' else '>';assert b[:2] in [b'II',b'MM'];assert struct.unpack(endian+'H',b[2:4])[0]==42
 pos=struct.unpack(endian+'I',b[4:8])[0];n=struct.unpack(endian+'H',b[pos:pos+2])[0];tags={}
 for i in range(n):
  e=b[pos+2+12*i:pos+14+12*i];tag,typ,count=struct.unpack(endian+'HHI',e[:8]);size={1:1,2:1,3:2,4:4,5:8,11:4,12:8}.get(typ)
  if size is None:continue
  v=e[8:12] if count*size<=4 else b[struct.unpack(endian+'I',e[8:12])[0]:][:count*size]
  if typ in [1,3,4]:tags[tag]=list(struct.unpack(endian+str(count)+{1:'B',3:'H',4:'I'}[typ],v[:count*size]))
 assert tags.get(259,[1])==[1] and tags.get(258)==[8] and tags.get(277,[1])==[1]
 W=tags[256][0];H=tags[257][0];offsets=tags[273];sizes=tags[279];a=b''.join(b[o:o+s] for o,s in zip(offsets,sizes));assert len(a)==W*H
 return W,H,a

def png(path,W,H,b):
 def chunk(t,p):return struct.pack('>I',len(p))+t+p+struct.pack('>I',binascii.crc32(t+p)&0xffffffff)
 raw=b''.join(b'\x00'+b[y*W*3:(y+1)*W*3] for y in range(H));path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

def main():
 with zipfile.ZipFile(P/'data/1_ClassicSingleCellTFM.zip') as z:
  for specimen in ['Pos004','Pos007','Pos008']:
   out=bytearray(512*512*3*3)
   for ch in range(3):
    names=[n for n in z.namelist() if '/Relaxed/' in n and re.search(specimen+r'_S001_z\d+_ch0'+str(ch)+r'\.tif$',n)];assert len(names)==376,(specimen,ch,len(names));mip=bytearray(512*512)
    for name in sorted(names)[::4]:
     W,H,a=tiff(z.read(name));assert (W,H)==(512,512)
     for k,v in enumerate(a):
      if v>mip[k]:mip[k]=v
    for y in range(512):
     for x in range(512):
      k=(y*1536+ch*512+x)*3;v=mip[y*512+x];out[k:k+3]=bytes([v,v,v])
   png(P/'evidence'/f'{specimen}-relaxed-channels-projection.png',1536,512,out)
 print('Reference-only projections saved: ch00 | ch01 | ch02; no measured displacement values read.')
if __name__=='__main__':main()
