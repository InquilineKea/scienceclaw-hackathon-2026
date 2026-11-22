#!/bin/bash
cd "$(dirname "$0")/.."
python3 scripts/04_dft.py 1 37 >> logs/dft.log 2>&1
python3 scripts/05_md.py helix 0.04 ff14SB ff99SB >> logs/md_helix_a.log 2>&1
