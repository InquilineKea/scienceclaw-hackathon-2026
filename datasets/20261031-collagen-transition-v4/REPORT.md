# Collagen transition atlas: H100 results and numerical audit

The revised suite completed on a real NVIDIA H100 80 GB. It passed 12 numerical checks and accepted 398 of 400 recorded mechanical states, with 34 of 36 fully converged recorded paths. The two failed states remain in the raw data and are excluded from eligible curves. This is a small, finite, dimensionless mechanistic study: one seed, 36 junctions, periodic two-dimensional networks. It does not identify a universally toughest collagen network or a real pressure/acceleration limit.

The revision responds to the seven-part critique by adding strain sweeps, plastic sliding and rupture, stiff-bond placement and adaptive damage, explicit inclusion contacts, load–hold–unload memory, a finite helix–coil statistical model, and an explicitly hypothetical LOX feedback system. Actual triple-helix melting MD remains unperformed. The LOX model is a new declared ODE, not a calibrated extension of the earlier H5 gain.

## Numerical coverage

| Mechanical experiment | Accepted states / recorded states | Fully converged recorded paths / cases |
|---|---:|---:|
| Strain-driven rigidity | 27 / 27 | 3 / 3 |
| Sliding and locking | 75 / 75 | 3 / 3 |
| Plastic-memory matrix | 144 / 144 | 8 / 8 |
| Sliding with rupture | 54 / 54 | 3 / 3 |
| Stiff-bond placement | 42 / 42 | 14 / 14 |
| Adaptive versus random cuts | 28 / 28 | 2 / 2 |
| Inclusion contact and compression | 28 / 30 | 1 / 3 |

Acceptance requires a fresh maximum absolute force residual below 3×10^-8 and an energy change no larger than 10^-8|E|+10^-14. The convergence repair adds a translation-fixed damped-Newton refinement to the existing L-BFGS minimization for small networks; it does not loosen these tolerances. This tests local force balance and energy settlement, not global minimality, uniqueness or a positive mechanical Hessian.

The contact failures are precisely identified: area fraction 0 at compression 0.45 (force residual 3.2640×10^-4), and area fraction 0.4 at compression 0.10 (1.82046×10^-2). Area fraction 0.75 converged at all ten recorded compression states. No biological jamming threshold is inferred from these three cases.

## What the saved results support

### 1. Strain changes mechanical response

Three target coordinations, z=3.0, 3.6 and 4.2, produce realized values 3.0, 3.6111 and 4.2222 because the finite graph has an integer number of edges. The shear grid runs from 0 to 0.8 in increments of 0.1. Nonaffinity peaks occur at sampled strains 0.4, 0.2 and 0.3 respectively. This small study therefore does not establish a monotonic critical-strain law. The plotted stiffness is a finite-difference estimate on that grid; its first interval is not an infinitesimal modulus measurement.

All three networks stiffen across the sampled range. The final interval estimates are approximately 0.22394, 0.22484 and 0.38233 in model units. Graph Laplacian values are retained as descriptors, but three finite networks cannot establish a universal spectral predictor or a thermodynamic critical exponent. The motivation is the strain-controlled network physics studied by [Sharma et al.](https://doi.org/10.1038/nphys3628) and [Jansen et al.](https://doi.org/10.1016/j.bpj.2018.04.043); this pilot is not a reproduction or fit of those experiments.

### 2. Equal initial stiffness can coexist with very different relaxation

The three locking cases use identical initial graphs and spring constants. Readback finds exactly zero difference in their saved pre-hold stresses. A hypothetical locking input changes mobility according to 2 exp(-6 locking); it is not an AGE concentration.

| Locking input | Stress retained after a two-unit hold | Recorded plastic dissipation |
|---:|---:|---:|
| 0 | 25.5600% | 0.0994898 |
| 0.5 | 86.4063% | 0.0264810 |
| 1 | 99.2491% | 0.00155128 |

These are internally controlled outcomes of the prescribed mobility law. They support separating initial stiffness from stress relaxation within this model. They do not measure glycation or simulate glucosepane, PYD or 4-HNE reactions. [Fessel et al.](https://doi.org/10.1371/journal.pone.0110948) and [Gautieri et al.](https://doi.org/10.1016/j.matbio.2016.09.001) motivate studying restricted sliding; their systems and parameters are not calibrated by these numbers.

With a shared 20% elastic bond-strain rupture threshold and tension sampled through 0.85 strain, the mobile case loses no bonds, while each more locked case loses 3 of 61 bonds (4.918%). All recorded states and rupture avalanches converge. None reaches the chosen 20% bond-loss endpoint, so all three failure-strain measurements are censored. No finite failure threshold or general toughness winner is established.

### 3. Stiffening and cutting depend on where changes occur

Stiffening every existing spring twentyfold changes the small-shear modulus from 0.00115060 to 0.00117273, about a 1.92% increase, while the bending law remains unchanged. Random and clustered partial stiffening give different intermediate values. This leaves graph connectivity fixed and does not demonstrate a rigidity-percolation transition.

At the first 5% removal step, random cutting retains about 2.347% of the initial tension, while adaptive high-tension cutting retains about 33.606%. By 10% removal both are below 0.3%; the sweep continues through 65%. The counterintuitive first-step ordering is retained rather than rewritten to fit an expected story. This is one very small network under fixed lateral confinement and tensile strain 0.12, not a population estimate or a lung-disease model. [Bates et al.](https://doi.org/10.1164/rccm.200611-1739OC) provide the motivating disease-network context.

### 4. Compression now includes finite contact forces

The high-area-fraction case grows from 2 overlapping disk pairs initially to 108 at compression 0.45, with a final compression reaction of 38.4411 model units. It is the only inclusion case whose entire recorded path converges. The lower-density cases have the two failures listed above. A stronger reaction does not by itself mean better toughness or recovery.

These are polydisperse disks attached at network junctions. Area fraction is two-dimensional; the measured reaction is a first-Piola component under uniaxial compression, not hydrostatic pressure or a biological cell-volume fraction. The model adds an explicit mechanism motivated by [van Oosten et al.](https://doi.org/10.1038/s41586-019-1516-5) and [Shivers et al.](https://doi.org/10.1073/pnas.2003037117), without claiming their experimentally relevant phase boundary.

### 5. History matters, but residual-strain estimates remain provisional

At shear amplitude 0.45 and locking 0, increasing hold time from 0.2 to 2 model units reduces retained stress from 77.966% to 30.787%. At locking 1, the corresponding values are 99.933% and 99.333%. The four amplitude-0.15 cases retain stress within numerical roundoff and have no resolved unloading zero-crossing; their residual-strain entries remain null, not zero.

Residual-strain estimates are not monotonic in locking. The main sliding sweep returns approximately 0.1308, 0.0218 and 0.0601. Its bisection uses a finite interval resolution, and the final zero-stress residual was not saved. The separate memory matrix uses interpolation over a coarse unloading grid. These values should not be presented as a robust biological memory ranking; weak stresses, branch selection and resolution need further examination. Explicit junction rebinding and fibre merging are absent. [Kim et al.](https://doi.org/10.1038/s41467-017-01011-7) and [Nam et al.](https://doi.org/10.1073/pnas.1523906113) motivate the history-dependent question.

### 6. Thermal sensitivity is an exact statistical calculation, not melting MD

The 81-site two-state model evaluates 18 declared Hyp/hydration/crosslink combinations at 117 dimensionless temperatures: 2,106 values. Every curve is bounded and monotonically decreasing. An independent probability/count recurrence agrees with the GPU transfer-matrix calculation to a maximum absolute difference of 2.14×10^-14.

The half-folded temperatures span 0.8–1.25 because the assumed stabilization coefficients impose that range. This is a transparent sensitivity demonstration, not an independent prediction. There is no Celsius conversion, matched avian–human comparison or atomistic melting trajectory. `THERMAL_MD_GATE.json` lists the missing chemical microstates, parameters, hydration controls, replicas and reversible/equilibrium sampling. The different assays in [Leikina et al.](https://doi.org/10.1073/pnas.032307099) and [Losso and Ogawa](https://doi.org/10.1111/jfbc.12059) cannot be equated through this model.

### 7. Feedback bistability is demonstrated only for the declared equations

The hypothetical model is dS/dt=0.25+aL−S, dC/dt=S^4/(1+S^4)−C, dL/dt=0.05+gC−L. Among 969 sampled coupling/gain pairs, 323 have two stable equilibria. At coupling a=1, the sampled gains 1.4 through 4.0 have two stable branches. These are grid-resolved observations, not precisely located bifurcation boundaries.

All 202 increasing/decreasing dynamic samples converge; the maximum matched branch separation is 3.8921 stiffness-proxy units. Independently evaluated equilibrium equations have residuals below 9×10^-16. This goes beyond inferring a switch from loop gain alone. It does not demonstrate measured LOX signaling, and the earlier H5 gain of 0.234 has no calibrated mapping into these new parameters. [Levental et al.](https://doi.org/10.1016/j.cell.2009.10.027) and [Ronceray et al.](https://doi.org/10.1073/pnas.1514208113) motivate the mechanism, not the numerical parameter values.

## Verification and preservation

The check suite covers the analytic triangular-lattice shear modulus, nonzero fibre and contact finite differences, rigid-motion invariance, zero-mobility and zero-contact controls, dissipative plastic updates, feedback bookkeeping and strict JSON export, probability bounds and CPU/GPU energy agreement. Fibre/contact derivative differences are 6.81×10^-12 and 8.27×10^-10 respectively.

The final download is 2,480,407 bytes with SHA-256 `73b0132a8c6eaf94435cb6a63d89305aed450b6856e324116223884a6245c70c`. All 74 archive members and the 42-file scientific manifest verify. A separate scalar-math calculation reproduces all 238 saved-frame energies to 2.85×10^-14; finite-difference force spot checks at the last converged frame of 22 cases have maximum residual 2.99×10^-9 at step 5×10^-6. No scientific package was imported locally for these readbacks. These checks corroborate implementation and saved states, not biological validity.

The raw stream contains every recorded protocol sample, including the failures. Suite JSON adds lattice context and derived quantities; figures include eight PNG/SVG pairs and two GIFs. Animations replay saved protocol states with convergence labels and omit edges crossing periodic boundaries. They are not atomistic trajectories or calibrated physical time. Internal optimizer iterates and intermediate plastic-hold substeps were not recorded. Later converged states do not validate an earlier failed path-dependent update.

| Real job ID | Outcome | Compute-equivalent estimate |
|---|---|---:|
| aijob-e00ngbb7wmy88429pa | Failed; archive writer could not seek on object storage; numerical outputs unavailable | $1.149 |
| aijob-e00rxabfzdn5yamng9 | Failed at NumPy-boolean JSON export; all written partial mechanics recovered; 82/400 converged | $0.916 |
| aijob-e00dv1sg6b68gbz2hp | Completed; 398/400 converged; full output recovered | $1.061 |

Total estimated compute-equivalent time is $3.126, below the authorized $15. The displayed rate was $4.51/hour including temporary disk and startup/shutdown. These are estimates, not an invoice; taxes, discounts and private object storage are not finalized. All three GPU jobs are stopped; no persistent new VM remains. A private output bucket is retained for recovery.

The first attempt's missing numerical data are a real preservation gap. Its source, console failure and cost record are retained; no later run is relabelled as that original output. Subsequent revisions verify storage before computation and export stage checkpoints. Prepared v3 was never launched. Rejected upload forms did not create compute jobs. The public archive keeps recoverable raw data byte-for-byte, while removing account navigation from provider-console captures with a redaction ledger. Each later run must use a new identity and checksum manifest.
