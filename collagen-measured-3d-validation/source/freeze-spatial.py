"""Original reference-only cell mask and prospective spatial eligibility; no displacement outcomes read."""
from pathlib import Path
import zipfile,struct,json,math,hashlib,itertools
from importlib.machinery import SourceFileLoader
P=Path(__file__).parent;I=SourceFileLoader('original_tiff',str(P/'inspect-images.py')).load_module()
B=128;D=94;VOX=[.7211,.7211,.988];THRESHOLD=12;INNER=30.;GUARD=35.

def main():
 with zipfile.ZipFile(P/'data/1_ClassicSingleCellTFM.zip') as z:
  for specimen in ['Pos004','Pos007','Pos008']:
   volume=bytearray(B*B*D)
   for iz in range(D):
    name=f'1_ClassicSingleCellTFM/Relaxed/Mark_and_Find_001/{specimen}_S001_z{iz*4:03d}_ch01.tif';w,h,a=I.tiff(z.read(name))
    for y in range(512):
     for x in range(512):
      k=(iz*B+y//4)*B+x//4;v=a[y*512+x]
      if v>volume[k]:volume[k]=v
   above=set(i for i,v in enumerate(volume) if v>=THRESHOLD);components=[];largest=[]
   while above:
    seed=above.pop();queue=[seed]
    for index in queue:
     x=index%B;y=index//B%B;zz=index//(B*B)
     for dx,dy,dz in itertools.product([-1,0,1],repeat=3):
      xx=x+dx;yy=y+dy;zt=zz+dz
      if not(0<=xx<B and 0<=yy<B and 0<=zt<D):continue
      j=(zt*B+yy)*B+xx
      if j in above:above.remove(j);queue.append(j)
    components.append(len(queue))
    if len(queue)>len(largest):largest=queue
   # Author convention: model x=image row, model y=image column, model z=slice.
   # Nodes are centered over PIV sample range; use full imaged-volume center for image-to-mesh map.
   pts=[[(i//B%B*4+1.5-255.5)*VOX[0],(i%B*4+1.5-255.5)*VOX[1],(i//(B*B)*4-187.5)*VOX[2]] for i in largest]
   buckets={}
   for q in pts:buckets.setdefault(tuple(math.floor(v/20) for v in q),[]).append(q)
   geom=json.loads((P/'data'/specimen/'geometry.json').read_text());nodes=[[v*1e6 for v in n] for n in geom['nodes']];bounds=[[min(n[d] for n in nodes),max(n[d] for n in nodes)] for d in range(3)];dist=[];boundary=[];score=[];excluded=[]
   for n in nodes:
    key=[math.floor(v/20) for v in n];best=1e9
    for shift in itertools.product(range(-4,5),repeat=3):
     for q in buckets.get(tuple(key[d]+shift[d] for d in range(3)),[]):
      dd=sum((n[d]-q[d])**2 for d in range(3))
      if dd<best:best=dd
    dc=math.sqrt(best);outer=min(min(n[d]-bounds[d][0],bounds[d][1]-n[d]) for d in range(3));fixed=outer<1e-6 or dc<=INNER
    boundary.append(fixed);score.append(outer>GUARD and dc>INNER+GUARD);dist.append(dc);excluded.append(dc<=INNER+GUARD)
   octants=[0]*8
   for n,s in zip(nodes,score):
    if s:octants[sum((n[d]>0)<<d for d in range(3))]+=1
   assert sum(score)>=200 and sum(v>=20 for v in octants)>=4,(specimen,sum(score),octants)
   out={'specimen':specimen,'source_geometry_sha256':hashlib.sha256((P/'data'/specimen/'geometry.json').read_bytes()).hexdigest(),'mask_reference':'Relaxed ch01 fluorescence; fixed threshold12,uint8,4xcoarse maxxy,sampled4z; largest26-connected component','voxel_size_um':VOX,'model_axes':'x=image row,y=image column,z=slice; static author source get_deformations.py','cell_samples_um':pts,'cell_mask_voxels':len(pts),'other_component_sizes':sorted(components,reverse=True)[1:10],'inner_prescribed_distance_um':INNER,'score_guard_um':GUARD,'boundary':boundary,'score':score,'cell_distance_um':dist,'counts':{'prescribed_nodes':sum(boundary),'reference_eligible_score_nodes':sum(score),'octants':octants},'scope':'Internal conditional spatial prediction; sampling mesh not measured collagen fiber connectivity; heldoutPos008; no displacement values used to choose masks'}
   (P/'data'/specimen/'frozen-mask.json').write_text(json.dumps(out,separators=(',',':')));print(specimen,out['counts'],'cellvoxels',len(pts))
 print('Masks frozen before displacement-outcome inspection. Full1Dmask arrays and source hashes retained.')
if __name__=='__main__':main()
