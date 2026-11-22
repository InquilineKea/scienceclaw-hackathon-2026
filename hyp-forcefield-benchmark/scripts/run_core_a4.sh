#!/bin/bash
cd "$(dirname "$0")/.."
while kill -0 1560 2>/dev/null; do sleep 5; done
python3 scripts/05_md.py helix 0.04 ff19SB >> logs/md_helix_a.log 2>&1
