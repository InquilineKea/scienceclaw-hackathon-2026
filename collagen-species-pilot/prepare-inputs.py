"""Original standard-library preparation; does not import or execute CDSM."""
import hashlib
import json
import pathlib
import shutil
import sys

project=pathlib.Path(__file__).resolve().parent
cache=project/'inputs'
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else project/'reprepared'
if out.exists():raise SystemExit('Choose a new output directory')
out.mkdir(exist_ok=True);(out/'inputs').mkdir(exist_ok=True);(out/'vendor'/'thparams').mkdir(parents=True,exist_ok=True)
specs=[('beaver','Castor_canadensis','COL1A1','A0A250Y7T0',175,1188),('beaver','Castor_canadensis','COL1A2','A0A8B7UHI7',91,1107),('human','Homo_sapiens','COL1A1','P02452',179,1192),('human','Homo_sapiens','COL1A2','P08123',91,1107)]
records=[];seq={}
for species,scientific,gene,acc,start,end in specs:
    r=json.loads((cache/f'{acc}.json').read_text());assert r['primaryAccession']==acc
    s=r['sequence']['value'];h=s[start-1:end]
    assert len(h)%3==0 and all(h[i]=='G' for i in range(0,len(h),3))
    (out/'inputs'/f'{acc}.json').write_text(json.dumps(r,indent=2)+'\n')
    (out/'inputs'/f'{acc}.fasta').write_text(f'>{acc} {scientific} {gene} full precursor\n'+s+'\n')
    records.append({'species':species,'scientificName':scientific.replace('_',' '),'gene':gene,'accession':acc,'entryType':r['entryType'],'fullLength':len(s),'sequenceSha256':hashlib.sha256(s.encode()).hexdigest(),'helicalStart':start,'helicalEnd':end,'helicalRegionMethod':'longest uninterrupted GXY run; human COL1A1 agrees with UniProt annotated triple-helical region','url':f'https://www.uniprot.org/uniprotkb/{acc}/entry'})
    seq[species,gene]=h
def alignment(a,b):
    # Needleman-Wunsch: match +2, mismatch -1, linear gap -3. Diagonal tie priority.
    n=len(b);prev=[-3*j for j in range(n+1)];trace=[bytearray(n+1)]
    for i,x in enumerate(a,1):
        cur=[-3*i]+[0]*n;t=bytearray(n+1);t[0]=1
        for j,y in enumerate(b,1):
            choices=(prev[j-1]+(2 if x==y else -1),prev[j]-3,cur[j-1]-3);k=max(range(3),key=lambda k:choices[k]);cur[j]=choices[k];t[j]=k
        trace.append(t);prev=cur
    i,j=len(a),len(b);aa=[];bb=[]
    while i or j:
        k=trace[i][j] if i and j else (1 if i else 2)
        if k==0:i-=1;j-=1;aa.append(a[i]);bb.append(b[j])
        elif k==1:i-=1;aa.append(a[i]);bb.append('-')
        else:j-=1;aa.append('-');bb.append(b[j])
    return ''.join(reversed(aa)),''.join(reversed(bb))
pairs=[]
for gene in ['COL1A1','COL1A2']:
    a,b=alignment(seq['beaver',gene],seq['human',gene]);gaps=a.count('-')+b.count('-')
    pairs.append({'gene':gene,'alignmentLength':len(a),'identicalResidues':sum(x==y for x,y in zip(a,b)),'identity':sum(x==y for x,y in zip(a,b))/len(a),'gaps':gaps})
    (out/'inputs'/f'{gene}-aligned.fasta').write_text(f'>beaver_{gene}\n{a}\n>human_{gene}\n{b}\n')
    assert gaps==0,'Revisit window correspondence: indel detected'
tasks=[];windowStats=[]
for name,offset in [('N',0),('middle',462),('C',924)]:
    for gene in ['COL1A1','COL1A2']:
        a,b=[seq[sp,gene][offset:offset+90] for sp in ['beaver','human']]
        windowStats.append({'window':name,'offset0':offset,'gene':gene,'identicalResidues':sum(x==y for x,y in zip(a,b)),'length':90,'differences':[{'windowPosition1':i+1,'beaver':x,'human':y} for i,(x,y) in enumerate(zip(a,b)) if x!=y]})
    for species in ['beaver','human']:
        for order in ['112','121','211']:
            chains=[seq[species,'COL1A'+g][offset:offset+90] for g in order]
            tasks.append({'id':f'{species}-{name}-{order}','species':species,'window':name,'helicalOffset0':offset,'order':order,'sequences':chains,'ptm':'gene-encoded sequence; CDSM getprop internally maps Y-position P to O for propensity lookup; no measured PTM assignment'})
metadata={'date':'2026-10-31','scope':'Matched 90-residue backbone commissioning only; no AGE chemistry, dynamics, stiffness, rupture or species robustness inference.','builderCommit':'074a6f3aa76c987fde3fa39746c33256429a081a','records':records,'alignments':pairs,'windows':windowStats,'tasks':tasks}
(out/'inputs'/'pilot.json').write_text(json.dumps(metadata,indent=2)+'\n')
source=project/'vendor'
shutil.copyfile(source/'step1_backbone_builder.py',out/'vendor'/'step1_backbone_builder.py')
shutil.copyfile(source/'LICENSE',out/'vendor'/'LICENSE')
for p in (source/'thparams').iterdir():shutil.copyfile(p,out/'vendor'/'thparams'/p.name)
print(json.dumps({'alignments':pairs,'windows':windowStats,'tasks':len(tasks)},indent=2))
