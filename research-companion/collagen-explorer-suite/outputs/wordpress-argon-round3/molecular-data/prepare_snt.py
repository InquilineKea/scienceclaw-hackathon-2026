from pathlib import Path
import zipfile,io,csv,json,struct,ast,math,collections,hashlib
R=Path(__file__).resolve().parent;D=R/'ready';B=Path('work/sites-round3/snt/dist');receipts=[]
def val(v):
 if v in ['True','False']:return v=='True'
 if v=='':return None
 try:x=float(v);return int(x) if x.is_integer() else x
 except (ValueError,TypeError):return v

def tab(z,path,id,title=None):
 r=csv.DictReader(io.StringIO(z.read(path).decode()));cols=r.fieldnames;rows=[[val(a[c]) for c in cols] for a in r];return {'id':id,'title':title or id,'columns':cols,'rows':rows}
def write(d):
 p=D/(d['id']+'.json');p.write_text(json.dumps(d,separators=(',',':'),allow_nan=False));print(d['id'],p.stat().st_size)
def npy(b):
 assert b[:6]==b'\x93NUMPY';v=b[6];off=10 if v==1 else 12;hlen=struct.unpack('<H' if v==1 else '<I',b[8:off])[0];h=ast.literal_eval(b[off:off+hlen].decode());assert not h['fortran_order'];shape=h['shape'];n=math.prod(shape);assert n<10000000
 codes={'<f4':'f','<f8':'d','<i8':'q','<i4':'i'};code=codes[h['descr']];raw=b[off+hlen:];assert len(raw)==n*struct.calcsize(code);return shape,list(struct.unpack('<'+str(n)+code,raw))
def npz(z,path):
 with zipfile.ZipFile(io.BytesIO(z.read(path))) as q:return {n[:-4]:npy(q.read(n)) for n in q.namelist()}
def frame(arr,i):
 shape,a=arr;assert len(shape)==3 and shape[2]==3;return [a[j:j+3] for j in range(i*shape[1]*3,(i+1)*shape[1]*3,3)]
def mean_xyz(xs):return [sum(p[i] for p in xs)/len(xs) for i in range(3)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def torsion(p):
 b0=sub(p[0],p[1]);b1=sub(p[2],p[1]);b2=sub(p[3],p[2]);l=math.sqrt(dot(b1,b1));b1=[x/l for x in b1];a=[x-dot(b0,b1)*y for x,y in zip(b0,b1)];b=[x-dot(b2,b1)*y for x,y in zip(b2,b1)];return math.degrees(math.atan2(dot(cross(b1,a),b),dot(a,b)))
def mol(t):
 a=t.splitlines();n=int(a[3][:3]);m=int(a[3][3:6]);nodes=[];elements=[]
 for l in a[4:4+n]:nodes.append([float(l[:10]),float(l[10:20]),float(l[20:30])]);elements.append(l[31:34].strip())
 bonds=[[int(l[:3])-1,int(l[3:6])-1,int(l[6:9])] for l in a[4+n:4+n+m]];return nodes,elements,bonds

# Ligand conformers: all36final structures, actual sampled trajectory frames only for archived12r0trajectories.
name='snt5382_atomistic_pilot';prefix=name+'/';z=zipfile.ZipFile(B/(name+'.zip'));assert sum(x.file_size for x in z.infolist())<40000000
rep=tab(z,prefix+'outputs/replicate_summary.csv','replicas','36short ligand-only trajectories');cond=tab(z,prefix+'outputs/condition_summary.csv','conditions','Mean±sample SD across3replica means');molecules=[];obs=[];cols=None;reach_checks=[]
for row in rep['rows']:
 r=dict(zip(rep['columns'],row));directory=prefix+'outputs/'+r['condition']+'/';nodes,elements,bonds=mol(z.read(directory+'final.mol').decode());initial,_,_=mol(z.read(directory+'initial.mol').decode());degree=collections.Counter()
 for i,j,k in bonds:
  if elements[i]!='H' and elements[j]!='H':degree[i]+=1;degree[j]+=1
 ns=[i for i,e in enumerate(elements) if e=='N'];am=[i for i in ns if degree[i]==1];ring=[i for i in ns if degree[i]==3];assert len(am)==len(ring)==1
 ot=tab(z,directory+'observables.csv','unused');cols=ot['columns'];obs+=ot['rows'];last=dict(zip(cols,ot['rows'][-1]));err=abs(math.dist(nodes[am[0]],nodes[ring[0]])-last['amine_reach_A']);assert err<.0003;reach_checks.append(err)
 o={'id':r['condition'],'name':r['variant'],'recordBinding':{'condition':r['condition'],'replica':r['replica'],'charge':r['charge'],'epsilon':r['epsilon']},'nodes':nodes,'initial_nodes':initial,'elements':elements,'bonds':bonds,'amine_index':am[0],'scaffold_n_index':ring[0],'units':'Å','final_time_ps':20,'frames':[]}
 if directory+'trajectory.xyz' in z.namelist():
  lines=z.read(directory+'trajectory.xyz').decode().splitlines();n=int(lines[0]);assert len(lines)%(n+2)==0
  for i in range(len(lines)//(n+2)):
   start=i*(n+2);time=float(lines[start+1].split('t_ps=')[1].split()[0]);xyz=[[float(x) for x in l.split()[1:4]] for l in lines[start+2:start+2+n]];o['frames'].append({'time_ps':time,'nodes':xyz})
 molecules.append(o)
d={'id':'snt-ligand-ensemble','title':'SNT-5382: actual ligand conformers and amine reach','postIds':[24],'sourceURLs':['https://snt5382-research-downloads.stochasticcockatoo.chatgpt.site/snt5382_atomistic_pilot.zip'],'evidence':'36short ligand-only MMFF94/OpenMM trajectories, no enzyme simulation','units':{'coordinates':'Å','amine_reach_A':'Å','time_ps':'ps'},'limitations':['20ps production perreplica after5ps equilibration; short preparation, not an equilibrium ensemble.','No LOXL2, copper, LTQ, explicit solvent or reactive chemistry; no potency or inhibition inference.','Dielectric78.4 only screens intramolecular electrostatics; it is not water/implicit solvation.','Both des-fluoro controls are computational scaffold edits; experimental reagent identity is not established.','All36final structures are saved. Time-resolved XYZ frames exist only for12replica0runs; missing trajectories are unavailable, never inferred.','Mean±SD across3replica means is distinct from correlated within-run frame variation.'],'tables':[rep,cond,{'id':'observables','title':'Saved perframe reach and geometry','columns':cols,'rows':obs}],'molecules':molecules,'validation':{'all36finalReachVsCSV_maxAbsoluteError_A':max(reach_checks),'finalMolCoordinatesFourDecimalPrecision':True,'trajectoryRepresentatives':sum(bool(x['frames']) for x in molecules)}};write(d);receipts.append({'archive':str(B/(name+'.zip')),'sha256':hashlib.sha256((B/(name+'.zip')).read_bytes()).hexdigest(),'dataset':d['id']});z.close()

# Hydroxylation: real48residue peptide C-alpha/ring coordinates and separately normalized216network rows.
name='collagen_hydroxylation_tensegrity';prefix=name+'/';z=zipfile.ZipFile(B/(name+'.zip'));assert sum(x.file_size for x in z.infolist())<40000000
reps=tab(z,prefix+'outputs/molecular_replicates.csv','molecular-replicas');validation=tab(z,prefix+'outputs/structural_validation.csv','structural-validation');trajectories=[];chirows=[];projections={};ca_frames={};max_chi_error=0
for rr in reps['rows']:
 r=dict(zip(reps['columns'],rr));case=r['condition']+'_r'+str(r['replica']);directory=prefix+'outputs/'+case+'/';arrays=npz(z,directory+'protein_trajectory.npz');coords=arrays['coordinates_A'];times=arrays['time_ps'][1];globalindices=arrays['protein_atom_indices'][1];mapping={v:i for i,v in enumerate(globalindices)};atoms=[]
 for l in z.read(directory+'initial_solvated.pdb').decode().splitlines():
  if l.startswith(('ATOM  ','HETATM')):atoms.append({'chain':l[21],'residue':int(l[22:26]),'resname':l[17:20].strip(),'atom':l[12:16].strip(),'element':l[76:78].strip()})
 lookup={(a['chain'],a['residue'],a['atom']):mapping[g] for g,a in enumerate(atoms) if g in mapping};ca=[lookup[(c,i,'CA')] for c in 'ABC' for i in range(1,17)];selected=list(ca)
 for c in 'ABC':
  for i in [3,6,9,12,15]:
   for a in ['N','CA','CB','CG','CD']+(['OD1'] if (c,i,'OD1') in lookup else []):
    n=lookup[(c,i,a)]
    if n not in selected:selected.append(n)
 inv={local:atoms[globalindices[local]] for local in selected};index={local:i for i,local in enumerate(selected)};edges=[[i*16+j,i*16+j+1] for i in range(3) for j in range(15)]
 for c in 'ABC':
  for i in [3,6,9,12,15]:
   ring=[lookup[(c,i,a)] for a in ['N','CA','CB','CG','CD']];edges += [[index[ring[j]],index[ring[(j+1)%5]]] for j in range(5)]
   if (c,i,'OD1') in lookup:edges.append([index[lookup[(c,i,'CG')]],index[lookup[(c,i,'OD1')]]])
 fs=[];angles=[];allcaf=[]
 for i,t in enumerate(times):
  x=frame(coords,i);fs.append({'time_ps':t,'nodes':[[round(v,6) for v in x[j]] for j in selected]});allcaf.append([x[j] for j in ca])
  for c in 'ABC':
   for rid in [6,9,12]:
    angle=torsion([x[lookup[(c,rid,a)]] for a in ['CA','CB','CG','CD']]);angles.append(angle);chirows.append([r['condition'],r['replica'],t,c,rid,angle])
 target=next(dict(zip(validation['columns'],x)) for x in validation['rows'] if dict(zip(validation['columns'],x))['condition']==r['condition'] and dict(zip(validation['columns'],x))['replica']==r['replica']);circ=math.degrees(math.atan2(sum(math.sin(math.radians(x)) for x in angles),sum(math.cos(math.radians(x)) for x in angles)));error=abs(circ-target['ring_chi2_circular_mean_deg']);assert error<1e-4;max_chi_error=max(max_chi_error,error)
 trajectories.append({'id':case,'name':r['condition'],'recordBinding':{'condition':r['condition'],'replica':r['replica']},'units':'Å','nodes':fs[0]['nodes'],'edges':edges,'groups':[inv[j]['chain'] for j in selected],'labels':[inv[j] for j in selected],'elements':[inv[j]['element'] for j in selected],'frames':fs,'hyp_sites':r['HYP_site_map'],'note':'Cα traces plus all15Y-site proline/hydroxyproline rings and retained hydroxyl oxygens; solvent omitted from display, not from original calculation.'});ca_frames[(r['condition'],r['replica'])]=allcaf
 # Preserve source global-index map for exact four-bead projection.
 projections[(r['condition'],r['replica'])]={'source_global_to_CA':{globalindices[c]:i for i,c in enumerate(ca)},'ca_nodes':allcaf[0],'ca_labels':[atoms[globalindices[c]] for c in ca]}
d={'id':'hydroxylation-prestress','title':'Hydroxylation geometry and independent prestress mechanics','postIds':[53],'sourceURLs':['https://snt5382-research-downloads.stochasticcockatoo.chatgpt.site/collagen_hydroxylation_tensegrity.zip'],'evidence':'12explicit-water20ps peptide pilots and independent216state normalized network benchmark','units':{'coordinates':'Å','time_ps':'ps','ring_chi2_deg':'degrees','network_stiffness':'normalized model units'},'limitations':['48residues total, truncated chains with charged termini; not fullcollagenI.','Each20ps production starts from an already folded helix; no melting, equilibrium stability or longevity ranking.','Two partial patterns each retain8/15Hyp sites with different placement.','Molecular trajectories do not calibrate the216prestress network parameters.','Ring χ2 distributions pooled from correlated frames are descriptive, not independent-sample uncertainty.'],'tables':[reps,validation,tab(z,prefix+'outputs/prestress_networks.csv','prestress-networks','Independent normalized prestress experiment'),{'id':'ring-puckering','title':'Central Y-site χ2 from saved trajectories (derived geometry; agrees with archived circular means)','columns':['condition','replica','time_ps','chain','residue','chi2_deg'],'rows':chirows}],'molecules':trajectories,'validation':{'derivedChi2VsArchivedCircularMeans_maxError_degrees':max_chi_error}};write(d);receipts.append({'archive':str(B/(name+'.zip')),'sha256':hashlib.sha256((B/(name+'.zip')).read_bytes()).hexdigest(),'dataset':d['id']});z.close()

# Four-bead calibration distributions from exact archived coordinates, no fitted Gaussian substitution.
name='collagen_lammps_calibration';prefix=name+'/';z=zipfile.ZipFile(B/(name+'.zip'));assert sum(x.file_size for x in z.infolist())<40000000
projection=json.loads(z.read(prefix+'inputs/projection_manifest.json'));maps=[];projected={}
for row in projection:
 key=(row['condition'],row['replica']);p=projections[key];groups=[[p['source_global_to_CA'][g] for g in group] for group in row['CA_groups']];pos=[mean_xyz([p['ca_nodes'][j] for j in ids]) for ids in groups];maps.append({'id':row['condition']+'_r'+str(row['replica']),'condition':row['condition'],'replica':row['replica'],'nodes':p['ca_nodes'],'labels':p['ca_labels'],'groups':[x['chain'] for x in p['ca_labels']],'edges':[[i*16+j,i*16+j+1] for i in range(3) for j in range(15)],'bead_positions_A':pos,'bead_groups':groups,'bead_edges':[[0,1],[1,2],[2,3]],'units':'Å','recordBinding':{'type':'exact_projection','condition':row['condition'],'replica':row['replica'],'time_ps':0},'label':'Exact9Cαcentroids perbead; each three-residue range across three chains; not chemical crosslinks.'});projected[key]=[[mean_xyz([f[j] for j in ids]) for ids in groups] for f in ca_frames[key]]
def internal(x):
 b=[math.dist(x[i],x[i+1]) for i in range(3)];a=[]
 for i in range(2):
  u=sub(x[i],x[i+1]);v=sub(x[i+2],x[i+1]);a.append(math.acos(max(-1,min(1,dot(u,v)/math.sqrt(dot(u,u)*dot(v,v))))))
 return b+a
hist=[];cgframes=[];moment_checks=[]
validation_table=tab(z,prefix+'outputs/validation.csv','validation-check');validation_map={(r[0],r[1],r[2]):dict(zip(validation_table['columns'],r)) for r in validation_table['rows']}
for row in projection:
 cond=row['condition'];held=row['replica'];case=cond+'_hold'+str(held);arr=npz(z,prefix+'outputs/'+case+'/trajectory.npz');cg=[internal(frame(arr['coordinates_A'],i)) for i in range(arr['coordinates_A'][0][0])];train=[internal(x) for rep in range(3) if rep!=held for x in projected[(cond,rep)]];test=[internal(x) for x in projected[(cond,held)]]
 for k,coord in enumerate(['bond1','bond2','bond3','angle1','angle2']):
  sets={'train':[x[k] for x in train],'heldout':[x[k] for x in test],'CG':[x[k] for x in cg]};lo=min(min(v) for v in sets.values());hi=max(max(v) for v in sets.values());width=(hi-lo)/32
  for label,vals in sets.items():
   target=validation_map[(cond,held,coord)];mean=sum(vals)/len(vals);sd=(sum((x-mean)**2 for x in vals)/len(vals))**.5;key={'train':'train','heldout':'test','CG':'CG'}[label];err=max(abs(mean-target[key+'_mean']),abs(sd-target[key+'_sd']));assert err<1e-5,(cond,held,coord,label,err);moment_checks.append(err)
   counts=[0]*32
   for x in vals:counts[min(31,max(0,int((x-lo)/width)))]+=1
   for i,n in enumerate(counts):hist.append([cond,held,coord,'Å' if k<3 else 'radian',label,lo+i*width,lo+(i+1)*width,n,len(vals),n/len(vals)/width])
 # Keep actual sparse savedCG snapshots, never interpolate missing dynamics.
 shape,_=arr['coordinates_A'];inds=sorted(set([0,shape[0]-1]+list(range(0,shape[0],500))));cgframes.append({'id':case,'condition':cond,'heldout_replica':held,'nodes':frame(arr['coordinates_A'],0),'edges':[[0,1],[1,2],[2,3]],'units':'Å','frames':[{'nominal_time_ps':arr['nominal_time_ps'][1][i],'nodes':frame(arr['coordinates_A'],i)} for i in inds],'recordBinding':{'type':'saved_CG_fold','condition':cond,'heldout_replica':held},'note':'Nominal CG time; no physical kinetic calibration.'})
d={'id':'four-bead-calibration','title':'From9Cαgroups to4beads: training fit versus held-out transfer','postIds':[69],'sourceURLs':['https://snt5382-research-downloads.stochasticcockatoo.chatgpt.site/collagen_lammps_calibration.zip'],'evidence':'12LAMMPS replica-holdout structural fits from short atomistic peptide references','units':{'bond':'Å','angle':'radian','K_bond':'kcal/mol/Å²','K_angle':'kcal/mol/radian²','force':'pN','CG_time':'nominal ps, not physical kinetic calibration'},'limitations':['Each bead is the equal-weight centroid of9Cαatoms:3residues×3chains. Fourbeads cover residue ranges2–4,5–7,8–10,11–13.','Three bonds/twoangles only; no solvent, nonbonded interactions, torsion or chemical crosslinks in the CGmodel.','Two fullreplicas fit each fold; the third is held out. Frames remain correlated.','Force intervals across folds are ranges, not confidence intervals or tissue-strength predictions.','Training match reaches0.24SD while excluded-replica mean errors reach1.84SD; short windows and missing coupling remain limits.','Histogram counts are directly derived from saved coordinates with common32bin edges per fold/coordinate; no Gaussian assumption/refitting.'],'tables':[tab(z,prefix+'outputs/replica_holdouts.csv','fold-parameters'),tab(z,prefix+'outputs/validation.csv','distribution-validation'),tab(z,prefix+'outputs/reference_window_diagnostics.csv','reference-window-diagnostics'),tab(z,prefix+'outputs/force_extension.csv','force-extension'),{'id':'distribution-histograms','title':'Actual saved-coordinate distributions (training/heldout/CG)','columns':['condition','heldout_replica','coordinate','unit','population','bin_low','bin_high','count','population_n','density'],'rows':hist}],'mappings':maps,'molecules':cgframes,'summary':json.loads(z.read(prefix+'outputs/summary.json')),'extraction_validation':{'savedValidationMoments180ChecksMaxAbsoluteError':max(moment_checks)}};write(d);receipts.append({'archive':str(B/(name+'.zip')),'sha256':hashlib.sha256((B/(name+'.zip')).read_bytes()).hexdigest(),'dataset':d['id']});z.close();(R/'snt-extraction-receipts.json').write_text(json.dumps(receipts,indent=2))
