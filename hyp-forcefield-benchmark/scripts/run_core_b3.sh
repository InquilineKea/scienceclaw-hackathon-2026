#!/bin/bash
cd "$(dirname "$0")/.."
while kill -0 1418 2>/dev/null; do sleep 5; done
python3 scripts/05_md.py helix 0.04 C36mGP C36m >> logs/md_helix_b.log 2>&1
