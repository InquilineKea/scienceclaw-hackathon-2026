# Completed CDSM backbone commissioning

The 2-vCPU Nebius job completed successfully. All 18 structures have 270 residues and 1,080 N/CA/C/O atoms, with 90 residues in each of chains A/B/C. The 405,910-byte output ZIP and all source/result manifest hashes were checked after download (see download-receipt.json for the exact archive byte count and SHA-256). Scientific-child runtime was about 0.281 seconds; the console reported 926 ms workload duration, excluding provisioning. The displayed instance price was $0.08/hour, with a $0.20 authorized ceiling; no invoice was retrieved.

The same-frame alpha-carbon coordinate differences across species span 0–1.812 Å across the nine matched window/order pairs. Two N-window orderings have identical backbone coordinates despite sequence differences, illustrating the coarseness of this deterministic geometry stage. These are not fitted structural RMSDs, stability scores or mechanical differences.

No AGE adduct, force field, solvent, relaxation, dynamics or rupture model was run. Network calibration remains null. The structures are starting material for a later matched chemical/mechanical study; no species robustness ranking follows from them.

The initial oversized file injection was rejected before job creation. The successful job read the same SHA-256-verified source payload through the private task bucket, then ran the pinned backbone module under UID/GID 65534 with verified socket denial. All actual executed scientific source is in source/; outputs are in result/. The original downloaded ZIP is preserved unchanged.
