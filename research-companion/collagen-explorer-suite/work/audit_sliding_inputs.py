"""Static molecular-data inventory; stdlib only. Does not import simulation code."""
from pathlib import Path
import collections, hashlib, json, math, shutil

ROOT = Path('/path/to/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs')
OUT = Path('/path/to/Codex/2026-10-30/referenced-chatgpt-conversation-this-is-an-2/outputs/hydrated-sliding-study')
OUT.mkdir(exist_ok=True)
sources = {
 'PYD': ROOT/'collagen-publication-20261031/native-crosslink-md/inputs/PYD/prepared.json',
 'DPD': ROOT/'collagen-publication-20261031/native-crosslink-md/inputs/DPD/prepared.json',
 'GLU_LINKED': ROOT/'collagen-candidate-publication-20261031/prepared/GLU_LINKED/GLU_LINKED.json',
 'GLU_CONTROL': ROOT/'collagen-candidate-publication-20261031/prepared/GLU_CONTROL/GLU_CONTROL.json',
}
records = []
for name, source in sources.items():
    raw = source.read_bytes(); d = json.loads(raw)
    target = OUT/'inputs'/name; target.mkdir(parents=True, exist_ok=True)
    dest = target/'prepared.json'
    if dest.exists() and dest.read_bytes() != raw:
        raise RuntimeError('Refusing to replace different input')
    if not dest.exists(): dest.write_bytes(raw)
    assert hashlib.sha256(dest.read_bytes()).digest() == hashlib.sha256(raw).digest()
    chains = collections.defaultdict(list)
    for i, a in enumerate(d['atoms']): chains[a['chain']].append((i,a))
    chain_records = []
    for chain, entries in chains.items():
        ca = [(i,a) for i,a in entries if a['name']=='CA']
        xyz = [a['xyz'] for _,a in ca]
        vec = [xyz[-1][k]-xyz[0][k] for k in range(3)]
        length = math.sqrt(sum(v*v for v in vec))
        chain_records.append({'chain':chain,'atoms':len(entries),'CA_atoms':[i for i,_ in ca],
          'CA_centroid_A':[sum(x[k] for x in xyz)/len(xyz) for k in range(3)],
          'CA_end_to_end_A':length,'CA_end_to_end_unit_vector':[v/length for v in vec],
          'modified_residues': sorted({(a['resindex'],a['resname']) for _,a in entries if a['resname'] in ('LYX','LY2','LY3','LXX','LX2','LX3','LGX','AGS')})})
    junctions=[]
    for j in d['audit']['junctions']:
        i,k=j['atoms']; a,b=d['atoms'][i],d['atoms'][k]
        junctions.append({'indices':[i,k],'chains':[a['chain'],b['chain']],
          'residues':[a['resname'],b['resname']], 'atom_names':[a['name'],b['name']],
          'distance_A':math.dist(a['xyz'],b['xyz'])})
    records.append({'model':name,'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),
      'atoms':len(d['atoms']),'net_charge_e':sum(a['q'] for a in d['atoms']),
      'chains':chain_records,'junctions':junctions,'reported_parameter_coverage':d['audit']['coverage_pass'],
      'native_unlinked_control_available_in_this_input_set':False if name in ('PYD','DPD') else None,
      'dynamic_validation_performed_by_this_audit':False})
(OUT/'input-audit.json').write_text(json.dumps({'models':records,'status':'static inventory only; no new MD executed'},indent=2)+'\n')
print(json.dumps([{'model':r['model'],'atoms':r['atoms'],'chains':len(r['chains']),'junctions':r['junctions']} for r in records],indent=2))
