"""Original analytic physical Hessian, remote NumPy/SciPy only.

Includes residual-weighted geometric terms omitted by Gauss--Newton.
No solver import; accepts the existing Model object. Inspect and validate
check_hvp on all frozen geometries before using a polish result.
"""
import math
import numpy as np
from scipy.sparse import coo_matrix

def physical_hessian(model, u, gamma, plane):
    u = np.asarray(u).reshape(-1, 3)
    v = model.v + u[model.jj] - u[model.ii]
    v[:, 0] += gamma * model.v[:, plane]
    length = np.maximum(np.linalg.norm(v, axis=1), 1e-15)
    n = v / length[:, None]
    I = np.eye(3)
    nn = n[:, :, None] * n[:, None, :]
    # J.T@J already contains the axial material and cosine gradient products.
    state = model.state(u.ravel(), gamma, plane, jac=True)
    H = state['J'].T @ state['J']
    q = ((length-model.rest)/(model.rest*length) * model.active)[:, None, None] * (I-nn)
    edge = np.concatenate((np.concatenate((q, -q), axis=2),
                           np.concatenate((-q, q), axis=2)), axis=1)
    na, nb = n[model.ai], n[model.aj]
    A, B = length[model.ai], length[model.aj]
    co = np.sum(na*nb, axis=1)
    aa = na[:, :, None]*na[:, None, :]
    bb = nb[:, :, None]*nb[:, None, :]
    ab = na[:, :, None]*nb[:, None, :]
    ba = nb[:, :, None]*na[:, None, :]
    Haa = (-ab-ba-co[:, None, None]*I+3*co[:, None, None]*aa)/A[:, None, None]**2
    Hbb = (-ab-ba-co[:, None, None]*I+3*co[:, None, None]*bb)/B[:, None, None]**2
    Hab = (I-aa-bb+co[:, None, None]*ab)/(A*B)[:, None, None]
    Q = np.concatenate((np.concatenate((Haa, Hab), axis=2),
                        np.concatenate((Hab.transpose(0, 2, 1), Hbb), axis=2)), axis=1)
    incidence = np.zeros((6, 12))
    incidence[:3, :3] = -I; incidence[:3, 3:6] = I
    incidence[3:, 6:9] = -I; incidence[3:, 9:12] = I
    angle = np.einsum('pi,aij,jq->apq', incidence.T, Q, incidence)
    am = model.active[model.ai] & model.active[model.aj]
    coeff = model.aw * (model.sg*co-model.c0) * model.sg * am
    angle *= coeff[:, None, None]
    # COO summation handles duplicated shared-junction coordinates correctly.
    rr = np.concatenate((np.broadcast_to(model.eids[:, :, None], edge.shape).ravel(),
                         np.broadcast_to(model.aids[:, :, None], angle.shape).ravel()))
    cc = np.concatenate((np.broadcast_to(model.eids[:, None, :], edge.shape).ravel(),
                         np.broadcast_to(model.aids[:, None, :], angle.shape).ravel()))
    vv = np.concatenate((edge.ravel(), angle.ravel()))
    extra = coo_matrix((vv, (rr, cc)), shape=(model.D, model.D)).tocsr()[3:, 3:]
    H = (H+extra).tocsr()
    return (H+H.T)*0.5

def check_hvp(model, u, gamma, plane, steps=(1e-5, 5e-6, 1e-6)):
    u = np.asarray(u).ravel()
    state = model.state(u, gamma, plane, jac=True)
    pre = 1/np.sqrt(np.maximum(np.asarray(state['J'].power(2).sum(axis=0)).ravel(), 1.))
    direction = np.sin(np.arange(model.D-3)*0.71+.3)
    direction /= np.linalg.norm(direction)
    physical_direction = pre*direction
    H = physical_hessian(model, u, gamma, plane)
    exact = pre*(H @ physical_direction)
    records = []
    for h in steps:
        du = np.r_[np.zeros(3), physical_direction*h]
        plus = model.state(u+du, gamma, plane)['grad'][3:]
        minus = model.state(u-du, gamma, plane)['grad'][3:]
        finite = pre*(plus-minus)/(2*h)
        relative = float(np.linalg.norm(finite-exact)/max(1e-12, np.linalg.norm(finite), np.linalg.norm(exact)))
        records.append(dict(h=float(h), relative_error=relative,
                            max_absolute_error=float(np.max(np.abs(finite-exact)))))
    return dict(records=records, passes=min(r['relative_error'] for r in records)<2e-4,
                definition='analytic physical Hessian action versus finite analytic-gradient differences')

def gradient_polish(model, start, gamma, plane, tol=1e-7, maxiter=12):
    """Near-equilibrium rescue only; tolerance and physical energy unchanged.

    Positive-clipped true-Hessian directions target a smaller physical residual.
    Energy increases are allowed only within a printed floating-point roundoff
    allowance, and every accepted trial must lower the actual max gradient.
    This does not certify stability; use the separate true-curvature screen.
    """
    u = np.asarray(start, dtype=float).ravel().copy()
    history = []
    for it in range(maxiter):
        state = model.state(u, gamma, plane, jac=True)
        residual = float(np.max(np.abs(state['grad'][3:])))
        if residual <= tol:
            break
        if residual > 1e-4:
            history.append(dict(iteration=it, status='outside_near_equilibrium_guard', residual=residual))
            break
        pre = 1/np.sqrt(np.maximum(np.asarray(state['J'].power(2).sum(axis=0)).ravel(), 1.))
        H = physical_hessian(model, u, gamma, plane).toarray()
        scaled = pre[:, None]*H*pre[None, :]
        values, vectors = np.linalg.eigh((scaled+scaled.T)*0.5)
        floor = 1e-8*max(1., float(np.max(np.abs(values))))
        gq = pre*state['grad'][3:]
        dq = -vectors @ ((vectors.T @ gq)/np.maximum(values, floor))
        step = np.r_[np.zeros(3), pre*dq]
        allowance = 64*np.finfo(float).eps*max(abs(state['E']), 1e-12)
        alpha = 1.; accepted = False
        for ls in range(35):
            trial = u+alpha*step
            candidate = model.state(trial, gamma, plane)
            next_residual = float(np.max(np.abs(candidate['grad'][3:])))
            if (math.isfinite(candidate['E']) and next_residual < residual and
                    candidate['E'] <= state['E']+allowance):
                history.append(dict(iteration=it, residual_before=residual, residual_after=next_residual,
                                    energy_change=float(candidate['E']-state['E']),
                                    roundoff_energy_allowance=float(allowance), alpha=alpha,
                                    minimum_scaled_eigenvalue=float(values[0])))
                u = trial; accepted = True
                break
            alpha *= .5
        if not accepted:
            history.append(dict(iteration=it, status='no_gradient_reducing_roundoff_safe_step', residual=residual))
            break
    state = model.state(u, gamma, plane)
    residual = float(np.max(np.abs(state['grad'][3:])))
    return u, state, residual, bool(residual <= tol and math.isfinite(state['E'])), history
