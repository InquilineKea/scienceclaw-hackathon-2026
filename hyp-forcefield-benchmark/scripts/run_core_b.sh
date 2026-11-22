#!/bin/bash
# core B: dipeptide MD in each force field's validated water, then the last triple-helix run
cd "$(dirname "$0")/.."
python3 scripts/05_md.py dipeptide 0.3 ff14SB ff99SB >> logs/md_dipeptide.log 2>&1
python3 scripts/05_md.py dipeptide 0.2 ff19SB C36m C36mGP >> logs/md_dipeptide.log 2>&1
python3 scripts/05_md.py helix 0.04 C36mGP >> logs/md_helix_b.log 2>&1
