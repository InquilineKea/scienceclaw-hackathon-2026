# ALCHEMI follow-up to matched-stiffness networks — 31 October 2026

Purpose: assess starting-conformer sensitivity in local crosslink-fragment force–extension curves before considering molecular inputs to the network study. This does not directly simulate the 2D network, its relaxation law, aging, YAP or organoid behavior.

Remote directory: `collagen-md-l40s-20261031:~/alchemi-matched-pilot-20261031` (direct host SSH port 22). Setup log: `pilot-retry.log`; first permission-failure log retained as `pilot.log`.

Protocol: reviewed NVIDIA Toolkit commit `84fe8e8fb8fab54863eea8f138722c7ab434966a`; MACE-OFF medium; eight pre-existing simplified neutral fragment proxies; RDKit seeds 101–103; nine engineering strains from −0.06 to 0.25; frozen anchor atoms; double precision FIRE2; up to 3000 steps per chemistry batch; target free-atom maximum force 0.02 eV/Å. One chemistry per batch bounds GPU memory. Compare final force with target before accepting a run. Nine scan points are exploratory, not a derivative-convergence study.

Setup is limited to 900 seconds and computation to 1800 seconds. Existing idle L40S reused, no new VM created. Only dedicated work and cache/environment volumes are mounted, with no credentials or personal files. Computation runs with network disabled. Residual supply-chain risks include pickle-capable upstream model weights, unpinned transitive dependencies and container-image provenance; environment freeze is saved. No claim of comprehensive fresh dependency verification is made.

Status at launch verification: setup completed, checkpoint cached, offline `alchemi-matched-run` container running. Driver reported 72 systems per conformer; Warp detected the L40S CUDA device. No completed molecular result verified yet. Outputs are `results/conformer_101.json` through `conformer_103.json`; success marker `PILOT_COMPLETED`. A JSON file alone is not acceptance: check finite energies, residual forces and boundary minima. Do not use these proxy curves as rupture forces or directly overwrite network parameters. Even accepted molecular stiffness estimates do not identify network relaxation time constants or selective axial-versus-bending relaxation.
