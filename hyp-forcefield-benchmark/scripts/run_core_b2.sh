#!/bin/bash
cd "$(dirname "$0")/.."
while kill -0 1418 2>/dev/null; do sleep 5; done
python3 scripts/05_md.py dipeptide 0.2 C36m C36mGP >> logs/md_dipeptide.log 2>&1
python3 scripts/05_md.py helix 0.04 C36mGP C36m ff19SB >> logs/md_helix_b.log 2>&1
