# Age-related crosslink hypothesis explorer

This is an original, dimensionless network experiment inspired by age-associated nonenzymatic crosslinking. It does not estimate a person's age, AGE concentration, tissue properties or clinical outcome. No numerical parameter is calibrated to glucosepane, pentosidine, methylglyoxal treatment or another chemical species. Baseline means **no added model connectors**, not a collagen specimen with no physiological crosslinks.

## Paired skeletons and added constraints

Build the same 36-node, 82-fiber collagen skeleton for each family/seed with the original model. Keep all reference coordinates, fiber areas, lengths, crimp, bending hinges, rupture thresholds and collagen volume (0.06) unchanged. Added connectors are stored separately from collagen fibers. They add their own elastic coupling without being counted as extra collagen volume. This is a fixed-collagen-budget comparison, not a fixed-total-elastic-energy or fixed-total-material comparison.

Candidate connectors join existing node pairs that are not already connected by a collagen fiber and are at most 0.46 reference-length units apart. A seeded random ordering gives distributed sites; a midpoint-distance score favors a central cluster. Increasing connector count selects a nested prefix of the same ordering. Both patterns have equal connector counts and spring stiffnesses, but their lengths and orientations can differ. Their contrast is a placement hypothesis, not a controlled isolation of clustering from every geometric covariate. A line crossing is not a new node or bending hinge.

For connector l with reference length L_l, current length r_l and stiffness k_l:

    U_l = (1/2) k_l (r_l − L_l)^2
    F_l = k_l (r_l − L_l)
    k_l = stiffness multiplier × median(A_e / L_e) of original fibers

The reference is a recruited axial-fiber stiffness scale, not the original toe-region tangent. The spring acts axially in extension and compression. It breaks irreversibly when (r_l − L_l)/L_l exceeds the chosen rupture extension; no healing or chemical kinetics are modeled. Breaking removes its stored energy, recorded as connector dissipation separately from collagen damage. The default hypothesis uses 12 connectors, a stiffness multiplier of 0.20, and rupture extension 0.30. Controls cover 0–24 connectors, multiplier 0–1, and rupture extension 0.05–0.80.

The original fiber law and collagen rupture thresholds do not change when connectors are added. Consequently, reduced extensibility is an outcome to test rather than a rule imposed by an 'old tissue' preset. Added connectors are effective constraints between network junctions: they do not resolve molecular sliding, amino-acid attachment sites or intra-/interfibrillar chemistry. Connectors remain until their own rupture criterion, even when nearby collagen fibers break.

## Loading, measurements and censoring

Use the directional experiment's constant boundary-node set: u = ε n[n · (X − c)], n = (cos θ, sin θ), c = (0.5, 0.5), on all 20 perimeter nodes. Both coordinates are prescribed, so transverse perimeter strain is zero. The 16 interior nodes relax by minimizing collagen plus connector energy. This is not the earlier free-lateral grip test. Angles θ and θ+180° impose the same strain.

Conjugate reaction is Σ_i gradient(U)_i · derivative(x_i, ε) at prescribed coordinates. Initial secant stiffness is reaction/strain at ε=0.002. Peak reaction, strain to criterion, collagen volume rupture and connector-count rupture are reported separately. Work integrates reaction dε by the trapezoid rule until 20% collagen volume is broken or reaction falls below half its running peak after ε>0.08 (peak>1e−5). Connector rupture alone does not trigger the collagen-volume stop. Work includes recoverable energy and is not irreversible dissipation alone, a measured tissue toughness, or crack fracture energy.

At ε=0.85 the experiment stops even if no failure criterion is reached. Such work is right-censored, shown with † or a hollow point; work ratios involving a capped or invalid endpoint are withheld. A failed equilibrium stops that trace immediately. The original compression-collapse regularization is retained and its activation is reported. Damage curves use different denominators: original collagen volume for fibers and initial connector count for connectors.

## Saved experiment and browser controls

The default benchmark consists of 504 connector runs: 7 families × 3 seeds (17,29,43) × 12 directions (0°–165° every 15°) × 2 placement patterns. Another 252 no-added-connector runs are freshly computed at matching resolution. The original 450-run and 252-run datasets remain unchanged. The seven-family table compares ratios of three-seed means at the nearest sampled angle; it always represents the default connector hypothesis, explicitly separate from custom sliders.

The live pair uses the exact chosen integer angle. Its curves compare one seed. Custom connector parameters trigger a new 12-direction worker sweep; the default hypothesis can use the saved sweep. All computation stays in the browser; no user input is uploaded. Export JSON preserves controls, model hashes, coordinates, damage, reaction curves and any completed angle sweep. Shared URLs retain the controls.

The numerical loading schedule includes zero, ε=0.002 and 480 increments to the cap. Free-force residual tolerance is 2e−9, with 4,800 iterations and one doubled-budget retry per relaxation. An 18-case spot check doubles the step count to 960 (three families × two patterns × three angles, seed 17). Exact diagnostics and censoring are in `data/aging.json`; the UI reports the maximum checked work change. The refined 756-run experiment contains no unconverged equilibria, with 10 capped connector runs and four capped baselines. Seventeen step-size checks changed work by less than 2%; the clustered disordered seed-17 specimen at 0° changed by 9.91%. That default case is marked step-sensitive, its angular work point is omitted, and its exact-angle/affected mean work ratio is withheld. Both coarse and finer work remain in the JSON. A ≥5% work change is a display flag, not a formal error bound. These checks do not establish convergence at every custom parameter choice.

Original tests verify unchanged collagen skeletons, nested connector selections, total-energy gradients against finite differences, rigid rotation/translation invariance, exact zero-connector and zero-stiffness controls, separate connector rupture energy accounting, and 180° periodicity. No third-party package or simulation code was installed or executed. The extension uses original code plus standard runtime APIs. Source review and numerical checks do not validate its biological assumptions.

## Evidence and distinctions

- [Fessel et al. (2014), PLoS ONE, doi:10.1371/journal.pone.0110948](https://pubmed.ncbi.nlm.nih.gov/25364829/): glycation changed molecular sliding and damage behavior in tendon experiments; mechanical changes differed across scales. This motivates studying constraints on relative motion, not assigning these springs a molecular identity.
- [Svensson et al. (2018), Acta Biomaterialia, doi:10.1016/j.actbio.2018.02.005](https://pubmed.ncbi.nlm.nih.gov/29447959/): methylglyoxal-treated rat-tendon fibrils became stronger and stiffer without induced brittleness. The experiment cautions against a universal 'more AGEs = brittle' rule.
- [Kamml et al. (2023), Journal of the Mechanical Behavior of Biomedical Materials, doi:10.1016/j.jmbbm.2023.106198](https://pubmed.ncbi.nlm.nih.gov/37890341/): coarse-grained fibril simulations varied AGE density and mechanical properties and found that these parameters affect deformation and failure. This is modeling context, not calibration data for the present network.

The network omits explicit molecular sliding/friction, viscoelastic relaxation, hydration, enzymatic remodeling, age-dependent turnover and cells. Non-crosslinking glycation modifications are not represented. Matching the direction of a literature effect would not validate this model; disagreement would identify a hypothesis or missing mechanism to investigate.
