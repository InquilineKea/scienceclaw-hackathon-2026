"""Independent finite-difference true-Hessian audit; execute only remotely.

No solver import. Pass an already constructed Model and an equilibrium u.
The callback must expose model.state(u, gamma, plane, jac=False) returning
E, grad and (with jac=True) J on free DOFs. This differentiates the actual
analytic gradient, including the residual-weighted terms omitted by J.T@J.
It neither changes equilibrium coordinates nor regularizes physical energy.
"""
import math
import time
import numpy as np

def check_state(model, u, gamma, plane, label, h=1e-5,
                equilibrium_tolerance=1e-7, relative_negative_tolerance=1e-5,
                hvp_tolerance=2e-3, symmetry_tolerance=2e-4):
    started = time.monotonic()
    u = np.array(u, dtype=float, copy=True).reshape(-1)
    D = len(u)
    if D < 6 or D > 1500:
        return dict(label=label, gamma=float(gamma), plane=int(plane),
                    classification='not_checked_size_guard', free_dofs=max(D-3, 0))
    if np.max(np.abs(u[:3])) > 1e-12:
        return dict(label=label, gamma=float(gamma), plane=int(plane),
                    classification='not_checked_gauge_mismatch', free_dofs=D-3)
    first = model.state(u, gamma, plane, jac=True)
    force = float(np.max(np.abs(first['grad'][3:])))
    common = dict(label=label, gamma=float(gamma), plane=int(plane),
                  free_dofs=D-3, max_free_gradient=force,
                  finite_difference_h=float(h),
                  scope='Selected equilibrium only; true-gradient finite-difference Hessian')
    if not math.isfinite(first['E']) or not np.isfinite(first['grad']).all():
        return dict(**common, classification='not_checked_nonfinite_state')
    if force > equilibrium_tolerance:
        return dict(**common, classification='not_equilibrated')

    # The scaling changes coordinates only; it preserves inertia/signature of
    # the exact Hessian. Uniform translations are already removed by the gauge.
    J = first['J']
    diagonal = np.asarray(J.power(2).sum(axis=0)).ravel()
    pre = 1.0 / np.sqrt(np.maximum(diagonal, 1.0))
    if len(pre) != D-3:
        return dict(**common, classification='not_checked_jacobian_shape')
    H = np.empty((D-3, D-3), dtype=float)
    evaluations = 1
    for j in range(D-3):
        plus = u.copy(); minus = u.copy()
        delta = h * pre[j]
        plus[j+3] += delta; minus[j+3] -= delta
        gp = model.state(plus, gamma, plane)['grad'][3:]
        gm = model.state(minus, gamma, plane)['grad'][3:]
        H[:, j] = pre * (gp-gm) / (2.0*h)
        evaluations += 2
    if not np.isfinite(H).all():
        return dict(**common, classification='not_checked_nonfinite_hessian',
                    state_evaluations=evaluations)
    asymmetry = float(np.max(np.abs(H-H.T)) / max(1.0, np.max(np.abs(H))))
    H = (H+H.T)/2.0

    # An independently directed central difference at half the column step
    # checks the matrix action without assuming the assembled Hessian is right.
    direction = np.sin(np.arange(D-3, dtype=float)*0.71 + 0.3)
    direction /= np.linalg.norm(direction)
    perturb = np.r_[np.zeros(3), pre*direction*(h/2)]
    gp = model.state(u+perturb, gamma, plane)['grad'][3:]
    gm = model.state(u-perturb, gamma, plane)['grad'][3:]
    fd_hvp = pre*(gp-gm)/h
    matrix_hvp = H @ direction
    hvp_error = float(np.linalg.norm(fd_hvp-matrix_hvp) /
                      max(1e-12, np.linalg.norm(fd_hvp), np.linalg.norm(matrix_hvp)))
    evaluations += 2
    eigenvalues, eigenvectors = np.linalg.eigh(H)
    lo, hi = float(eigenvalues[0]), float(eigenvalues[-1])
    scale = max(1.0, float(np.max(np.abs(eigenvalues))))
    cutoff = relative_negative_tolerance * scale
    nnegative = int(np.sum(eigenvalues < -cutoff))
    # Confirm the weakest mode with energy and gradient directional curvatures
    # at two distinct amplitudes, including cases classified marginal.
    vmin = eigenvectors[:, 0]
    curvature = []
    for step in (h, h/2):
        du = np.r_[np.zeros(3), pre*vmin*step]
        plus = model.state(u+du, gamma, plane)
        minus = model.state(u-du, gamma, plane)
        energy_curvature = float((plus['E']-2*first['E']+minus['E'])/step**2)
        gradient_curvature = float(vmin @ (pre*(plus['grad'][3:]-minus['grad'][3:]))/(2*step))
        curvature.append(dict(step=float(step), energy=energy_curvature,
                              gradient=gradient_curvature))
        evaluations += 2
    directional_negative = all(c['energy'] < -cutoff/2 and c['gradient'] < -cutoff/2
                               for c in curvature)
    qualified = asymmetry <= symmetry_tolerance and hvp_error <= hvp_tolerance
    if not qualified:
        classification = 'unresolved_finite_difference_accuracy'
    elif lo < -cutoff:
        classification = 'negative_curvature_confirmed' if directional_negative else 'unresolved_negative_mode'
    elif lo > cutoff:
        classification = 'positive_curvature_at_checked_state'
    else:
        classification = 'no_resolved_negative_curvature_marginal'
    return dict(**common, classification=classification,
                minimum_scaled_eigenvalue=lo, maximum_scaled_eigenvalue=hi,
                negative_eigenvalues_below_cutoff=nnegative,
                negative_cutoff=float(cutoff), symmetry_error=asymmetry,
                relative_hvp_error=hvp_error, weakest_direction_curvatures=curvature,
                state_evaluations=evaluations, seconds=time.monotonic()-started,
                physical_energy_regularization=False)
