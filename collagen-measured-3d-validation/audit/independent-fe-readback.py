"""Independent stdlib readback of frozen predictions; no solver/package import or refit."""
from pathlib import Path
import json,math,hashlib
P=Path(__file__).resolve().parents[1]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def element_geometry(x,t):
 a=x[t[0]];v=[[x[t[k]][d]-a[d] for d in range(3)] for k in [1,2,3]];c=[cross(v[1],v[2]),cross(v[2],v[0]),cross(v[0],v[1])];det=dot(v[0],c[0]);g=[[q/det for q in row] for row in c];g=[[-sum(row[d] for row in g) for d in range(3)]]+g;return abs(det)/6,g

def operator(nodes,tets,u,kind,nu,shift=(0.,0.,0.)):
 force=[0.]*(3*len(nodes));energy=0.;lam=2*nu/(1-2*nu) if kind=='elastic' else 0.
 for t in tets:
  vol,g=element_geometry(nodes,t);H=[[sum((u[3*t[a]+i]+shift[i])*g[a][j] for a in range(4)) for j in range(3)] for i in range(3)]
  if kind=='harmonic':sigma=H;energy+=vol*sum(q*q for row in H for q in row)/2
  else:
   eps=[[(H[i][j]+H[j][i])/2 for j in range(3)] for i in range(3)];tr=sum(eps[i][i] for i in range(3));sigma=[[2*eps[i][j]+(lam*tr if i==j else 0.) for j in range(3)] for i in range(3)];energy+=vol*(lam*tr*tr/2+sum(q*q for row in eps for q in row))
  for a,node in enumerate(t):
   for i in range(3):force[3*node+i]+=vol*dot(sigma[i],g[a])
 return force,energy

def main():
 specimen='Pos008';f=json.load(open(P/(specimen+'-fields.json')));r=json.load(open(P/(specimen+'-results.json')));g=json.load(open(P/'data'/specimen/'geometry.json'));mask=json.load(open(P/'data'/specimen/'frozen-mask.json'));m=json.load(open(P/'data'/specimen/'measured.json'));N=len(g['nodes']);nodes=[[v*1e6 for v in row] for row in g['nodes']];boundary=[a and b for a,b in zip(mask['boundary'],m['valid'])];score=[a and b for a,b in zip(mask['score'],m['valid'])];count=sum(boundary);offset=[sum(m['u'][i][d]*1e6 for i in range(N) if boundary[i])/count for d in range(3)];observed=[[m['u'][i][d]*1e6-offset[d] for d in range(3)] if m['valid'][i] else None for i in range(N)]
 assert boundary==f['boundary'] and score==f['score'];assert max(abs(a-b) for n,q in zip(nodes,f['nodes']) for a,b in zip(n,q))<1e-12
 centering=max(abs(q[d]-f['targets'][i][d]) for i,q in enumerate(observed) if q is not None for d in range(3));assert centering<1e-12
 measured=[v if row else 0. for row in observed for v in (row if row else [0.,0.,0.])];out=[]
 for model in r['results']:
  name=model['name'];u=f['predictions'][name];blocks=[{'n':0,'error2':0.,'observed2':0.} for _ in range(8)]
  for i in range(N):
   if not score[i]:continue
   k=sum((int(nodes[i][d]>0)<<d) for d in range(3));blocks[k]['n']+=1;blocks[k]['error2']+=sum((u[3*i+d]-observed[i][d])**2 for d in range(3));blocks[k]['observed2']+=dot(observed[i],observed[i])
  mse=sum(b['error2']/b['n'] for b in blocks)/8;record={'name':name,'equal_octant_MSE_um2':mse,'equal_octant_RMSE_um':math.sqrt(mse),'reported_MSE_difference':abs(mse-model['metrics']['primary_equal_octant_vector_MSE_um2']),'blocks':blocks};assert record['reported_MSE_difference']<1e-11
  if 'kind' in model:
   kind=model['kind'];nu=model.get('nu') or 0.;force,energy=operator(nodes,g['tetrahedra'],u,kind,nu);gb=[measured[i] if boundary[i//3] else 0. for i in range(3*N)];kg,_=operator(nodes,g['tetrahedra'],gb,kind,nu);rhsnorm=math.sqrt(sum(v*v for i,v in enumerate(kg) if not boundary[i//3]));residual=math.sqrt(sum(v*v for i,v in enumerate(force) if not boundary[i//3]))/max(rhsnorm,1e-30);moved,movedE=operator(nodes,g['tetrahedra'],u,kind,nu,shift=(.7,-1.2,2.3));translation_error=math.sqrt(sum((a-b)**2 for a,b in zip(force,moved)))/max(math.sqrt(dot(force,force)),1e-30);boundary_error=max(abs(u[3*i+d]-observed[i][d]) for i in range(N) if boundary[i] for d in range(3));energy_work=abs(energy-dot(u,force)/2)/max(abs(energy),1e-30);record.update(independent_relative_free_residual=residual,boundary_value_max_error_um=boundary_error,operator_translation_relative_difference=translation_error,energy_half_u_Ku_relative_difference=energy_work,energy_translation_relative_difference=abs(energy-movedE)/max(abs(energy),1e-30));assert residual<1e-7 and boundary_error<1e-12 and translation_error<1e-10 and energy_work<1e-10
  out.append(record)
 result={'specimen':specimen,'scope':'Independent stdlib readback of frozen field predictions, no parameter fit or test reselection','source_hashes':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['linear-fe.mjs','spatial-validation.mjs',specimen+'-results.json',specimen+'-fields.json']},'boundary_mean_offset_um':offset,'max_centered_target_difference_um':centering,'supplied_valid_boundary_nodes':count,'missing_prescribed_boundary_nodes':sum(mask['boundary'])-count,'heldout_valid_nodes':sum(score),'results':out};(P/'audit/INDEPENDENT-FE-READBACK.json').write_text(json.dumps(result,indent=2));print(json.dumps({**{k:v for k,v in result.items() if k not in ['results','source_hashes']},'models':[{k:v for k,v in a.items() if k!='blocks'} for a in out]},indent=2))
if __name__=='__main__':main()
