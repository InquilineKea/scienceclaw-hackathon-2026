#!/bin/bash
# core A: priority DFT single points (first 37 planned jobs), then triple-helix MD
cd "$(dirname "$0")/.."
python3 scripts/04_dft.py 1 37 >> logs/dft.log 2>&1
python3 scripts/05_md.py helix 0.04 ff14SB ff99SB ff19SB C36m >> logs/md_helix_a.log 2>&1
