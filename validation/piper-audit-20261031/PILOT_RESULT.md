# Approved atlas pilot — completed

Run: `atlas-sixcase-20261031T230849Z-e24e4e64`

Six fixed-seed cases passed against the archived same-source baseline. Source model SHA-256: `f0a5034f44aa7065c779f6e20209cd95ee13c7a3ffe6f3e40ae08172a7a489c1`.

| Architecture | Loading | Work | Peak reaction | Final damage fraction | Passed |
| --- | --- | ---: | ---: | ---: | --- |
| aligned | tension | 0.0005141879531 | 0.004875295038 | 0.2043473935 | yes |
| isotropic | confined | 1.847761728e-05 | 8.319221195e-05 | 0 | yes |
| isotropic | free | 4.323465196e-30 | 0 | 0 | yes |
| isotropic | pulse | 0.001466815938 | 0.007422942182 | 0.1695270709 | yes |
| isotropic | shear | 0.0003033775499 | 0.001679050027 | 0.07008646744 | yes |
| isotropic | tension | 0.0004034793391 | 0.002096007846 | 0.09933942919 | yes |

All quantities are dimensionless model outputs. All four equilibrium cases have maximum residual below 2e-7. The constrained pulse relative energy-balance error is 0.000332434 (0.03324%), below its 0.1% screen. The free-translation case has negligible internal work and zero damage, but its external/kinetic energy integration mismatch is 0.1924%; this case was tested as a rigid-translation control, not against the constrained-pulse energy threshold.

Scientific execution finished in 0.779888 seconds, exit 0. The two-minute timeout was not reached. Network-denial and outside-file-read-denial probes passed. All 17 files in the successful run manifest were verified. No cloud resources or paid jobs were used.

Earlier startup failures are retained in separate attempt folders. They occurred before scientific model execution: nested sandbox creation was denied; Node then needed its installed runtime libraries and root-directory metadata; an explicit CommonJS package boundary prevented it from inspecting a package file in the user home directory. No credential access was enabled.

This establishes same-source repeatability of six cases. It is not an independent solver implementation, full 450-case reproduction, cross-geometry robustness study, Python-patch regression, or biological calibration.

Python regressions are prepared and awaiting separate local-execution approval. Frozen baseline folders have not been changed.
