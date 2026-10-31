"""Remote-only runner of the pinned, separately reviewed CDSM backbone stage."""
import json,pathlib,sys,math,hashlib,time
here=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(here/'vendor'))
import step1_backbone_builder as cdsm
inputs=json.loads((here/'inputs'/'pilot.json').read_text())
out=pathlib.Path(sys.argv[1]);out.mkdir(exist_ok=False)
started=time.time();results=[];ca={}
for task in inputs['tasks']:
    chains=cdsm.build_backbone(task['sequences'],mode='core')
    assert len(chains)==3 and all(len(c)==90 for c in chains)
    assert all(''.join(r['one_letter'] for r in c)==s for c,s in zip(chains,task['sequences']))
    coords=[list(r['atoms']['CA']) for c in chains for r in c]
    assert all(math.isfinite(x) for c in coords for x in c)
    pdb=out/(task['id']+'.pdb');cdsm.write_backbone_pdb(str(pdb),chains)
    ca[task['id']]=[list(r['atoms']['CA']) for c in chains for r in c]
    spans=[max(r['atoms']['CA'][0] for r in c)-min(r['atoms']['CA'][0] for r in c) for c in chains]
    results.append({'id':task['id'],'species':task['species'],'window':task['window'],'order':task['order'],'residues':270,'atoms':sum(len(r['atoms']) for c in chains for r in c),'axialSpanAngstromByChain':spans,'pdbSha256':hashlib.sha256(pdb.read_bytes()).hexdigest()})
pairs=[]
for w in ['N','middle','C']:
    for order in ['112','121','211']:
        a,b=ca[f'beaver-{w}-{order}'],ca[f'human-{w}-{order}']
        # Builder-frame coordinate difference. No structural superposition or mechanics interpretation.
        rms=math.sqrt(sum(sum((x-y)**2 for x,y in zip(p,q)) for p,q in zip(a,b))/len(a))
        pairs.append({'window':w,'order':order,'builderFrameCaRmsDifferenceAngstrom':rms})
summary={'status':'completed','builderCommit':inputs['builderCommit'],'structureCount':len(results),'elapsedSeconds':time.time()-started,'scope':inputs['scope'],'results':results,'pairedGeometry':pairs,'caCoordinates':ca,'molecularToNetworkCalibration':None,'ageDamageSimulationPerformed':False,'speciesRobustnessConclusion':None}
(out/'backbones.json').write_text(json.dumps(summary,indent=2)+'\n')
manifest={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()}
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'status':'completed','structures':len(results),'seconds':time.time()-started}))
