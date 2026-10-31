# Directional mechanical anisotropy

This is a new, explicitly constrained directional-tension experiment. It uses the original dimensionless network energy, relaxation and rupture laws, whose model SHA-256 is `f0a5034f44aa7065c779f6e20209cd95ee13c7a3ffe6f3e40ae08172a7a489c1`. `directional.js` supplies a separate boundary protocol, loading schedule and stopping rule. The existing 450-run dataset, eight grip/body-force protocols and published ZIPs are unchanged.

## Boundary protocol

The reference square remains fixed in orientation. Set n = (cos θ, sin θ), center c = (0.5, 0.5), and impose u(X) = ε n [n · (X − c)] on every original perimeter node. Both coordinates of the 20 boundary nodes are prescribed; the 16 interior nodes minimize network energy with the original solver. The nominal deformation gradient at the boundary is I + ε n⊗n. Boundary transverse strain is zero; transverse stress is not prescribed to vanish. Arrow lengths are schematic, not force magnitudes.

This choice keeps the constrained node set identical at every angle and avoids discontinuous grip selection near a corner. It measures the mechanical response of the finite network **and this boundary condition**, not an intrinsic boundary-independent Young's modulus. In particular, θ = 0°/90° is not interchangeable with the original free-lateral X/Y grip tests. Changing supports can change the anisotropy.

Angles are axes of extension: n and −n give the same imposed strain. Therefore 180° equals 0°, and the final chart point repeats the computed 0° result. The remaining chart segments merely join sampled points; they are not additional simulations.

## Measures

The generalized reaction is Fε = Σ_boundary (∂U/∂x_i) · (∂x_i/∂ε), so Fε dε is external work. Initial secant stiffness is Kθ = Fε(0.002)/0.002, after interior relaxation and before damage. It is a small-strain secant, not an exact infinitesimal derivative.

Wθ = ∫ Fε dε uses trapezoidal integration and ends at the first of: (a) at least 20% of the original fiber volume has ruptured; (b) reaction below half of the running peak after ε > 0.08, provided the peak exceeded 1e−5. This is a protocol-defined toughness proxy / work density. It includes recoverable stored energy as well as dissipated energy and is **not** a crack fracture energy or a measurement of irreversible dissipation alone. Unit reference area and thickness set the dimensionless work-density normalization. There is no load-path connectivity stop in this perimeter protocol.

The strain cap is 0.85. If no criterion is reached, the run is right-censored; a hollow marker and † mark its recorded protocol work. A mean containing a capped run is also marked and is not treated as observed mean work to failure. Work anisotropy max/min is withheld if any sampled direction is capped or invalid. Invalid equilibria stop immediately and do not enter work curves. Stiffness validity is tracked independently at the probe.

## Dataset and numerical checks

Seven architectures × three seeds (17, 29, 43) × twelve directions (0° to 165° in 15° increments) = **252 new runs**. Every run uses the same default parameters and volume budget as its original network family; material topology and rupture thresholds do not change as the direction changes. The main pair's custom assumption controls do not alter this independent directional dataset.

The loading schedule includes 0, 0.002, and up to 240 equal increments to 0.85. Force residual tolerance is 2e−9, with up to 4,800 iterations plus one doubled-budget retry per relaxation. All 252 runs met their equilibrium tolerance; five aligned-network runs reached the strain cap.

Nine spot checks (aligned, disordered and loop-rich, seed 17, angles 0°, 45°, 90°) were repeated at 480 increments and at a tenfold tighter force tolerance. Halving the load step changed criterion work by at most 1.374%; tightening force tolerance changed initial stiffness by at most 0.0421%. These are bounded numerical checks, not a guarantee over every seed, angle or custom parameter. An exploratory coarser 120-step run exhibited a 22% work change at loop-rich 45° and was superseded before publication. Brittle rupture events make step resolution consequential.

Additional original tests cover boundary derivatives, zero reference energy, virtual-work consistency, 180° periodicity, a single-fiber analytical stiffness, covariance under rotation of both network and loading direction, censoring, and the expected aligned-network directional contrast.

Charts can display one seed or the mean of all three; whiskers show sample SD for the selected network. Ratios use extrema on the 15° grid, not a continuous optimization. The angle slider performs a fresh browser-worker solve at any integer angle for the selected network and seed (seed 17 in mean mode). The downloadable exact-angle JSON includes both model and directional-source hashes, parameters, frames, curves and diagnostics.

## Files and execution boundary

`data/directional.json` contains all metrics and sensitivity checks; `data/directional.csv` is tabular; `data/directional-data.js` is the same data packaged for a buildless static browser. `directional-runs/20261031-perimeter-v1/` freezes the inputs, outputs and checks with hashes. `benchmark-directional.js` only writes to a new explicitly named directory and refuses an existing destination.

No dependency was installed, and no third-party script, repository hook, cloud workload or model checkpoint was executed for this extension. The original code uses the unchanged authored model and standard runtime APIs. Browser computation is local with no data-upload endpoint, external library or CDN. This implementation review does not validate the hypothetical constitutive law or its biological interpretation.
