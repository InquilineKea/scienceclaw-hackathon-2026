"""Copy a bounded, buildless browser application into the GitHub Pages /docs source."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent
source=root/'collagen-network-atlas';dest=root/'docs'
files=['index.html','style.css','app.js','model.js','load-guide.js','worker.js','METHODS.md','EVIDENCE.md','data/benchmark.js','data/replays.js','data/results.json','data/summary.csv','data/curves.csv','figures/benchmark.svg','directional.js','directional-ui.js','directional-worker.js','DIRECTIONAL_METHODS.md','data/directional-data.js','data/directional.json','data/directional.csv','aging.html','aging.css','aging.js','aging-ui.js','aging-worker.js','AGING_METHODS.md','data/aging-data.js','data/aging.json','data/aging.csv']
files += ['density-ui.js','density.css','DENSITY_METHODS.md','data/density-data.js','data/density.json','data/density.csv','species.html','species.css','species-ui.js','SPECIES_METHODS.md','data/species-data.js','data/species-inputs.json','data/species-backbones.json']
files += ['TOPOLOGY_AGING_FIGURE.md','topology-aging.html','topology-aging.css','topology-aging.js','topology-figure.js','data/topology-maps.js','figures/topology-aging-overview.svg','figures/topology-aging-overview.png','figures/topology-aging-values.json']
files += ['force-replay/'+n for n in ['index.html','replay-ui.js','replay-data.js','replay.json','force-redistribution.gif','force-redistribution-still.png','README.md','VALIDATION.json']]
dest.mkdir(exist_ok=True)
allowed=set(files)|{'.nojekyll','DEPLOYMENT.json'}
unexpected=[str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and str(p.relative_to(dest)) not in allowed]
if unexpected:raise SystemExit('Unexpected files in Pages directory; review before replacing: '+str(unexpected))
density=json.loads((source/'data/density.json').read_text())
species=json.loads((source/'data/species-backbones.json').read_text())
assert len(density['rows'])==6300 and density['resolution']['displayed']==960, 'Never publish smoke data as the full sweep'
assert species['status']=='completed' and species['structureCount']==18
view_keys=['family','seed','angle','count','pattern','stiffness','work','failureStrain','workBeforeDamage','workBeforeCollagenDamage','stiffnessUnresolved','workUnresolved','failureStrainUnresolved','workBeforeDamageUnresolved','workBeforeCollagenDamageUnresolved']
view={key:value for key,value in density.items() if key!='rows'}
view['rows']=[{key:row[key] for key in view_keys} for row in density['rows']]
(source/'data/density-data.js').write_text('globalThis.ATLAS_DENSITY_DATA='+json.dumps(view,separators=(',',':'))+';\n')
for name,digest in density['sourceHashes'].items():
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
for name in files:
    target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
(dest/'.nojekyll').write_text('')
data=json.loads((source/'data/results.json').read_text())
model_hash=hashlib.sha256((source/'model.js').read_bytes()).hexdigest()
assert data['modelHash']==model_hash
directional=json.loads((source/'data/directional.json').read_text())
aging=json.loads((source/'data/aging.json').read_text())
assert directional['modelHash']==aging['modelHash']==model_hash
assert directional['directionalHash']==aging['directionalHash']==hashlib.sha256((source/'directional.js').read_bytes()).hexdigest()
assert aging['agingHash']==hashlib.sha256((source/'aging.js').read_bytes()).hexdigest()
metadata={'site':'Fracture Atlas','model_sha256':model_hash,'baseline_runs':len(data['rows']),'historical_archive_snapshot':'02b533d81e2de8a05227ab37284f2f553398735c','directional_runs':252,'aging_runs':len(aging['rows'])+len(aging['baseline']),'aging_source_sha256':aging['agingHash'],'directional_source_sha256':hashlib.sha256((source/'directional.js').read_bytes()).hexdigest(),'scope':'Original 450-run baseline, 252-run directional-strain experiment, and separate paired crosslink experiment. Static application and browser-local computation; no server or package installation.','files':{name:{'bytes':(dest/name).stat().st_size,'sha256':hashlib.sha256((dest/name).read_bytes()).hexdigest()} for name in files}}
metadata.update(density_configurations=6300,density_solver_runs=12600,cdsm_backbone_structures=18,cdsm_source_commit=species['builderCommit'])
metadata['scope']+=' Density sweep uses 6,300 paired configurations at two resolutions. Separate CDSM species pilot contains backbone geometry only, without molecular mechanical calibration.'
(dest/'DEPLOYMENT.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({'pages_source':'docs','files':len(files)+2,'bytes':sum(r['bytes'] for r in metadata['files'].values()),'model_sha256':model_hash}))
