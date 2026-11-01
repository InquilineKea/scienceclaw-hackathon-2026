#!/usr/bin/env python3
"""Verify exported bytes and exact scientific-data correspondence (stdlib only)."""
import argparse, hashlib, json, math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('study',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1]; site=root/'site' if (root/'site').exists() else root.parent/'docs/research-companion/fiber-rigidity'
m=json.loads((site/'data/manifest.json').read_text())
for f in m['artifact_files']:
    b=(site/f['path']).read_bytes()
    assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'], f['path']
src=a.study/'raw/results/work-stage2-attempt4/expanded-16x16/viewer.json'
assert hashlib.sha256(src.read_bytes()).hexdigest()==m['visualization']['source_viewer_sha256']
x=json.loads(src.read_text()); curves=json.loads((site/'data/curves.json').read_text()); n=0; max_periodic_error=0
for c,original in zip(curves,x['curves']):
    assert {k:v for k,v in c.items() if k!='frames_file'}==original
    frames=json.loads((site/c['frames_file']).read_text())
    expected=[f for f in x['network_frames'] if f['z_target']==c['z_target'] and f['kappa']==c['kappa']][::4]
    assert frames==expected
    for f in frames:
        b=f['box'];det=b[0][0]*b[1][1]-b[0][1]*b[1][0]
        def fractional(v):return [(v[0]*b[1][1]-v[1]*b[1][0])/det,(-v[0]*b[0][1]+v[1]*b[0][0])/det]
        for edge,v in zip(f['edges'],f['edge_vectors']):
            # Endpoint equivalence modulo periodic cell, independently of drawing.
            p0=f['positions'][edge[0]];p1=f['positions'][edge[1]]
            difference=fractional([p0[0]+v[0]-p1[0],p0[1]+v[1]-p1[1]])
            err=max(abs(d-round(d)) for d in difference);max_periodic_error=max(max_periodic_error,err)
            assert err<1e-10
            assert max(abs(t) for t in fractional(v))<1, 'Viewer copy range insufficient'
        n+=1
assert n==186
summary=json.loads((a.study/'SUMMARY.json').read_text())
assert json.loads((site/'data/seed-onsets.json').read_text())==summary['seed_curves']
print(json.dumps({'status':'pass','files_sha256':len(m['artifact_files']),'curves_exact':6,'frames_exact':n,'seed_onsets_exact':18,'max_periodic_endpoint_error':max_periodic_error},indent=2))
