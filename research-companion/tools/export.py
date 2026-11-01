#!/usr/bin/env python3
"""Original stdlib-only adapter: audited fiber viewer JSON -> static companion.
Reads data only. Never imports or executes the simulation repository.
Usage: python3 tools/export.py /path/to/outputs/fiber-rigidity-sweep
"""
import argparse, hashlib, json, shutil
from pathlib import Path

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('study',type=Path); a=ap.parse_args()
    root=Path(__file__).resolve().parents[1]; out=root/'site' if (root/'site').exists() else root.parent/'docs/research-companion/fiber-rigidity'; data=out/'data'
    data.mkdir(parents=True,exist_ok=True)
    src=a.study/'raw/results/work-stage2-attempt4/expanded-16x16/viewer.json'
    x=json.loads(src.read_text()); summary=json.loads((a.study/'SUMMARY.json').read_text())
    assert len(x['curves'])==6 and len(x['network_frames'])==726
    curves=x['curves']; bundles=[]
    for i,c in enumerate(curves):
        frames=[f for f in x['network_frames'] if f['z_target']==c['z_target'] and f['kappa']==c['kappa']]
        assert len(frames)==121 and all(f['seed']==0 and f['converged'] for f in frames)
        frames=frames[::4]
        assert len(frames)==31 and frames[-1]['gamma']==1
        name=f'data/frames-{i}.json'; write(out/name,frames)
        c['frames_file']=name
        bundles.append({'path':name,'frames':31,'seed':0})
    write(data/'curves.json',curves); write(data/'seed-onsets.json',summary['seed_curves'])
    for name in ['curve-summary.csv','seed-summary.csv','REPORT.md']:
        shutil.copyfile(a.study/name,data/name)
    manifest={
      'schema_version':'1.0','experiment_id':'fiber-rigidity-gcp-20261101',
      'title':'When does a fiber network stiffen?', 'date':'2026-11-01',
      'article_url':'https://humanavianaisymbiosis.wordpress.com/2026/11/01/gcp-fiber-rigidity-sweep-scienceclaw-onset-comparison/',
      'status':'completed_numerical_study','model':{'dimensions':2,'description':'Athermal periodic phantom triangular fiber network; harmonic stretching and same-fiber angular bending.','units':'Dimensionless model units','protocol':'Independent affine-start local minimizations, not a quasistatic loading trajectory.'},
      'design':{'precursor':[16,16],'retained_nodes':[238,256],'target_coordination':[3.2,3.5,3.8],'bending_kappa':[0.001,0.01],'paired_topology_seeds':[0,1,2],'strains':121,'strain_range':[0.001,1],'expanded_states':2178},
      'sources':[{'repository':'https://github.com/Sentinelayer-AIdenID/fiber-rigidity-sweep','commit':'5dcdca9676f29d66e63a2b665dfdb85d7173f039'},{'repository':'https://github.com/lamm-mit/scienceclaw','commit':'894598cd3a90891a077c254566276bd379038bad','patch':'Reviewed metadata.category integration patch'}],
      'validation':{'expanded_converged':2178,'expanded_total':2178,'demonstration_converged':72,'tighter_tolerance_converged':16,'max_tight_stress_relative_difference_percent':0.0524945,'independently_audited_states':2266,'setup_failures_retained':4,'conditional_fits_numerically_resolved':10,'conditional_fits_total':12},
      'visualization':{'curves':'Three-seed means, all 121 saved strain samples. Seed table gives individual onset estimates, not individual full curves.','network':'Seed 0 only; 31 actual saved states per parameter pair, every fourth strain. Slider selects discrete equilibria, not a time animation.','color':'Stretch energy per edge or half-hinge bending energy attributed to neighboring edges; log scale normalized within each frame.','frame_bundles':bundles,'source_viewer_sha256':digest(src)},
      'limits':['Not a 3D collagen or molecular structure model.','No decorin or fibronectin chemistry, assembly, binding or unfolding.','No thermal fluctuations or excluded volume.','Three seeds and one size do not establish finite-size scaling.','Operational onset definitions disagree; conditional exponents are not universal critical exponents.','Convergence does not prove global energy minima.'],
      'raw_archive':{'filename':'gcp-fiber-rigidity-results.tar.gz','bytes':26448567,'sha256':'4f3cda7b6f868da3052d329b7fa858531399f865d8b73e3f8d9ac2aa30ada065','availability':'Retained locally; not included in this compact companion.'},
      'compute':{'mode':'precomputed_only','public_job_submission':False},
      'artifact_files':[]}
    for p in sorted(data.iterdir()):
        if p.name!='manifest.json':manifest['artifact_files'].append({'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':digest(p)})
    write(data/'manifest.json',manifest)
    print(json.dumps({'curves':6,'frames':186,'artifact_files':len(manifest['artifact_files']),'data_bytes':sum(p.stat().st_size for p in data.iterdir())}))
if __name__=='__main__':main()
