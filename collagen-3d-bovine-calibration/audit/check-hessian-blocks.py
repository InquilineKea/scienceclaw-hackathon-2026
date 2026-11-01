"""Independent stdlib finite-difference checks of the proposed analytic Hessian blocks."""
import json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def outer(a,b):return [[x*y for y in b] for x in a]
def mul(M,v):return [dot(row,v) for row in M]
def norm(v):return math.sqrt(dot(v,v))
def angle_grad_hess(v,c0,sg,w):
 a,b=v[:3],v[3:];A,B=norm(a),norm(b);na=[x/A for x in a];nb=[x/B for x in b];co=dot(na,nb);err=sg*co-c0
 da=[(nb[k]-co*na[k])/A for k in range(3)];db=[(na[k]-co*nb[k])/B for k in range(3)];dc=[sg*x for x in da+db];grad=[w*err*x for x in dc]
 aa,bb,ab,ba=outer(na,na),outer(nb,nb),outer(na,nb),outer(nb,na);Q=[[0.]*6 for _ in range(6)]
 for i in range(3):
  for j in range(3):
   eye=float(i==j);Q[i][j]=(-ab[i][j]-ba[i][j]-co*eye+3*co*aa[i][j])/A**2;Q[i+3][j+3]=(-ab[i][j]-ba[i][j]-co*eye+3*co*bb[i][j])/B**2;Q[i][j+3]=(eye-aa[i][j]-bb[i][j]+co*ab[i][j])/(A*B);Q[j+3][i]=Q[i][j+3]
 H=[[w*(dc[i]*dc[j]+err*sg*Q[i][j]) for j in range(6)] for i in range(6)]
 return grad,H
records=[];models=json.load(open(P/'models.json'))
for m in models:
 if m['pattern']!='baseline':continue
 for k,(ei,ej,sg) in enumerate(m['a'][:8]):
  a=m['v'][ei][:];b=m['v'][ej][:];a[0]+=.03*a[1];b[0]+=.03*b[1];v=a+b;d=[math.sin(i*.8+.2) for i in range(6)];dn=norm(d);d=[x/dn for x in d];grad,H=angle_grad_hess(v,m['c0'][k],sg,m['aw'][k]);exact=mul(H,d);h=1e-6*min(norm(a),norm(b));gp=angle_grad_hess([x+h*y for x,y in zip(v,d)],m['c0'][k],sg,m['aw'][k])[0];gm=angle_grad_hess([x-h*y for x,y in zip(v,d)],m['c0'][k],sg,m['aw'][k])[0];fd=[(p-n)/(2*h) for p,n in zip(gp,gm)];relative=norm([x-y for x,y in zip(exact,fd)])/max(norm(exact),norm(fd),1e-12);records.append(dict(seed=m['seed'],angle=k,relative_Hvp_error=relative));assert relative<1e-4
out={'scope':'Independent stdlib check of analytic cosine Hessian blocks, 32 deformed angles','all_pass':True,'max_relative_Hvp_error':max(r['relative_Hvp_error'] for r in records),'records':records};(Path(__file__).parent/'hessian-block-checks.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
