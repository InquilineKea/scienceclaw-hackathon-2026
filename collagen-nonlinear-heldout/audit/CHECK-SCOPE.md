# Scope of numerical checks

CHECKS.json records4052 assertions, not4052 independent tests. Four thousand are repeated irreversibility checks along one prescribed scalar loading cycle; the remaining assertions cover quadrature moments, constitutive derivatives, finite-element energy gradients, rotations and normalization. The independent constitutive audit, JS/C++ crosschecks (including nonzero previous slip), exact-spectrum Ritz tests and full-state numerical controls provide separate implementation evidence.

These verify mathematical/numerical consistency of the stated surrogate. They do not validate collagen chemistry, fiber connectivity, sample history, image-correlation uncertainty or biological generalization. Positive axial tangents alone do not establish finite-strain equilibrium stability; compression contributes a geometric Hessian term. The bounded final-state screen includes that term but cannot prove absence of every unstable mode.
