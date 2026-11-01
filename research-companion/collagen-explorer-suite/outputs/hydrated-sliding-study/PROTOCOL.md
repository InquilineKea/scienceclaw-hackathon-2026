# Hydrated collagen sliding: protocol and execution gates

Status: Brev direct-host access repaired; bounded explicit-water H100 cycles executing. Final accepted counts and exclusions are reported in STATUS.md.

## Question and primary comparison

Measure resistance to small relative axial sliding of hydrated collagen peptide assemblies, with native PYD/DPD reference crosslinks and a glucosepane-linked/unlinked comparison. The molecular coupons differ in valence, peptide context, length and charge. They cannot provide a chemistry-only ranking across PYD, DPD and glucosepane. The existing glucosepane pair changes net solute charge from approximately +1 to -1 e; the resulting change includes ion/solvent response.

The static inventory preserves four original prepared models byte for byte: PYD (1793 solute atoms), DPD (1792), GLU_LINKED (481), GLU_CONTROL (471). `input-audit.json` records hashes, chain identities, CA axes and complete interchain crosslink atom identities. PYD and DPD each have six peptide segments and two crosslink graph edges; glucosepane has two segments and one crosslink graph edge. Ordinary-LYS-restored native unlinked controls were reconstructed as complete residues with hydrogens, charges, bonded terms and exclusions, then revalidated. Free hydroxylysine parameters were unavailable; hydroxylation and net charge remain confounded. These are not hydroxylation-matched precursor controls. Merely deleting a crosslink bond was not used.

## Geometry and chemistry gates

1. Verify input hashes and reproduce prior dry physical-system energy/force checks. Preserve source terms, units, exclusions, 1-4 scaling, chirality and protonation. Check CPU/CUDA agreement on identical hydrated coordinates.
2. Audit native chain grouping against source fibril identity before choosing the sliding groups. Candidate native groups are A/B/C and J/K/L; glucosepane uses A and B. Roughly parallel CA axes alone do not establish whole-fibril geometry.
3. Define a common axial coordinate from the selected backbone groups, with explicit endpoint/COM selection and weak, declared transverse/orientation restraints. Log the actual relative displacement, bias-center displacement, applied force and restraint work separately. Check periodic unwrapping and force signs with finite differences before dynamics.
4. Reuse source-compatible explicit water and ion models. Report actual box-volume salt-pair concentration, neutralizing ions and padding. Release preparation restraints before collecting response. Do not infer equilibrium from temperature and density alone.

## Staged execution

Use one verified idle H100. First attempt has a one-hour wall ceiling, with a small geometry/stability/throughput pilot before allocating the rest of that window. No duplicate dynamics, extra VM, or unbounded retry. The initial duration is a pilot budget and cannot establish converged free energies by itself.

First perform a reversible small-displacement axial ramp with native controls and glucosepane pair at two loading rates and both displacement directions. Target displacement must remain within a strain range that passes bond/geometry checks; choose it after the zero-load reference geometry is inspected. Sample force frequently enough to resolve the pulling protocol. Save all trajectories, biases, reaction forces, box histories, restarts, runtime versions and failures. Short high-rate work is a protocol-dependent mechanical measurement, not an equilibrium binding free energy.

Use independently prepared starting conformations/solvent arrangements where practical. Velocity seeds from one structure are conditional replicas, not independent conformational sampling. At least three replicas are needed for the initial variability check; more sampling is contingent on convergence and throughput. Compare slow/fast and forward/reverse responses before accepting a transferable slope. Failure of these checks is an outcome to retain, not a reason to fit a universal stiffness.

If sliding free energies are needed, add overlapping umbrella windows along the validated coordinate, decorrelation/effective-sample-size checks, forward/reverse initialization and block-based uncertainty. Only a sufficiently sampled, restraint-qualified potential of mean force may be reported as such. A mean pulling curve is not a PMF.

## Molecular-to-network transfer gate

Transfer a distribution of local force-versus-slip laws over the actually sampled displacement/rate range. Keep numerical, replica and molecular-model uncertainty separate. Report any dependence on transverse/orientation restraints. Do not map the molecular ps scale directly to cell-scale seconds, infer bond rupture from fixed-topology MD, or substitute coupon stiffness for whole-fiber EA.

In the network, introduce an explicit internal slip variable at junctions alongside stretching and bending. The microscopic connection density, attachment geometry and number of molecular links per junction remain uncertain mapping variables. Compare uniform versus clustered placement under both fixed microscopic laws and explicitly stiffness-matched conditions. Check energy balance, quasi-static force balance, timestep/refinement behavior and independent seed pairs.

For the adhesion experiment, impose a declared cell-shaped cavity and fixed contractile-displacement protocol at identified sites. Save the full reaction-force vector and displacement history at every site, not just their mean. Report normalized force if the mapping to physical junction density and geometry remains uncalibrated. A separate cell model is required for YAP/TAZ predictions.

## Public explorer acceptance

Publish only measured molecular outputs and validated network responses. Add provenance, model/replica counts, loading rates, interval construction, exclusions and transfer assumptions. Preserve the original adhesion model and matched-stiffness dataset. Exercise every new selector, force/interval readout, desktop/mobile layout, downloads and direct section link. Failed or unresolved calculations must remain labeled. No new results section should imply execution while the H100 remains inaccessible.

## Runtime security

Reuse the prior hash-pinned OpenMM 8.6.1, NumPy 2.5.4 and CUDA-12 wheel set and pinned Python container only after verifying actual wheel hashes against the saved lock. The hash-verified scientific wheels execute remotely in the reviewed isolation; none were installed or imported locally. Review the new task driver before remote execution. Native binaries, incomplete build attestation and the Docker/GPU boundary remain residual risks. Use an offline non-root container, read-only root and inputs, minimal writable outputs, no home/SSH/credential/Docker-socket mounts, dropped capabilities and resource limits. Never expose cloud credentials to the simulation.

References: https://docs.openmm.org/latest/userguide/theory/03_custom_forces.html ; https://manual.gromacs.org/current/reference-manual/special/pulling.html

## Executed protocol choices

Six prepared molecular systems; three velocity seeds each; two forward/reverse ramp durations, 40 and 80 ps. Each cycle contains 50 ps zero-command baseline, 0.04 nm forward ramp, 20 ps hold, reverse ramp, and 20 ps recovery: 170 or 250 ps total. One conformation and solvent build per model. NVT 310 K, 1 fs integration, explicit TIP3P, neutralizing ions, centroid axial/transverse bias coefficients 5000/1000 kJ mol^-1 nm^-2. Molecular curves saved every 1 ps, solute coordinate frames every 5 ps, final hydrated state/system and restart saved. No full solvent trajectory or equilibrium sampling claim.

Transfer gate: positive apparent force/slip slope, observed slip span >0.015 nm, and force-versus-command R² >0.3. Apparent slope is the ratio of fitted force-versus-command to slip-versus-command slopes. Force is k(q-s), so direct force-versus-instantaneous-slip regression would create a negative measurement correlation. Gates were not weakened after viewing outcomes.

Attempt 003 replaces clashing initial native-control sidechains with complete rotamer-searched LYS geometry. Its force finite-difference check isolates the pulling-bias energy to avoid solvent-background cancellation, keeping the same absolute tolerance and mechanics. Accepted attempt-002 trajectories are retained; only the failed glucosepane control cycle and native controls are supplied by attempt 003.

Published Martini 3 native-crosslink benchmark: author SI and Figure3 reference archives downloaded, catalogue MD5/SHA256/ZIP CRC verified, inventory retained. No author scripts executed and no independent Martini dynamics or full fibril force-response reproduction completed. This remains a gate before physical calibration.
