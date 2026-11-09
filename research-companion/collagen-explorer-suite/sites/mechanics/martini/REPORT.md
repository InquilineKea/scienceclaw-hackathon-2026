# Martini collagen benchmark attempt: validation failure

The HLKNL production trajectory failed with LINCS constraint warnings at approximately0.587ns. The intended45ns trajectory was not completed, the30ns equilibration exclusion was not reached, and PYD production did not start. No post-equilibration molecular benchmark result or molecular-to-network calibration is available.

The exact archived preconditioned initial structures were recovered and their initial cap lengths matched the sparse archived reference trajectories. Single-frame CPU/GPU and pulling-force/axial-virial numerical comparisons passed. These checks did not establish dynamical stability. The root cause of the subsequent constraint failure remains unresolved; it could involve runtime/protocol details and is not evidence by itself that the published model is invalid.

The attempted system uses the published native HLKNL topology, with relative cap forces, extended listed-pair table range and adjusted neighbor-list settings documented in failure-report.json. It does not simulate glucosepane. The native precursor files are unminimized, geometry-only PYD/DPD hydroxylation-pattern controls. They are not validated executable controls; the recovered ff03 HYL parameter candidate is not a validated drop-in replacement for the inherited Amber99 force field.

A separate CPU sensitivity study is complete and is explicitly dimensionless. At identical instantaneous stiffness, changing selected/background sliding time can reverse clustered-minus-uniform adhesion-force contrasts. It does not become molecularly calibrated by association with this failed MD attempt.

Primary sources: https://pubmed.ncbi.nlm.nih.gov/41074457/ and https://doi.org/10.17617/3.MF8BBT .
