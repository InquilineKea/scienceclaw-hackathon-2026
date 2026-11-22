#!/bin/bash
cd "$(dirname "$0")/.."
while kill -0 1560 2>/dev/null; do sleep 5; done
python3 scripts/05_md.py dipeptide_endo 0.1 C36m ff99SB >> logs/md_dipeptide.log 2>&1
