"""Quantum-chemistry reference for Ace-Hyp-NMe.

Geometries : GFN2-xTB (tblite) constrained optimisations driven by geomeTRIC.
Energies   : DFT single points (PySCF, density fitting) on those geometries.
"""
import os
import tempfile

import numpy as np

BOHR = 0.52917721092  # Angstrom
HARTREE_KCAL = 627.509474


def make_engine(symbols, xyz_ang):
    import geometric.engine
    import geometric.molecule
    from tblite.interface import Calculator

    numbers = np.array([{"H": 1, "C": 6, "N": 7, "O": 8}[s] for s in symbols])

    class TBLiteEngine(geometric.engine.Engine):
        def __init__(self, mol):
            super().__init__(mol)

        def calc_new(self, coords, dirname):
            calc = Calculator("GFN2-xTB", numbers, coords.reshape(-1, 3))
            calc.set("verbosity", 0)
            calc.set("accuracy", 0.1)
            res = calc.singlepoint()
            return {"energy": float(res.get("energy")), "gradient": np.array(res.get("gradient")).ravel()}

    m = geometric.molecule.Molecule()
    m.elem = list(symbols)
    m.xyzs = [np.array(xyz_ang, float)]
    return TBLiteEngine(m)


def xtb_opt(symbols, xyz_ang, set_dihedrals=None, maxiter=300):
    """Constrained optimisation.  set_dihedrals: list of ((i,j,k,l) 0-based, value_deg).

    Returns (xyz_ang, energy_hartree)."""
    import geometric.optimize

    engine = make_engine(symbols, xyz_ang)
    with tempfile.TemporaryDirectory() as tmp:
        kw = dict(customengine=engine, input=os.path.join(tmp, "job.xyz"), maxiter=maxiter,
                  logIni=None, convergence_set="GAU")
        if set_dihedrals:
            cons = os.path.join(tmp, "cons.txt")
            with open(cons, "w") as f:
                f.write("$set\n")
                for (i, j, k, l), v in set_dihedrals:
                    f.write(f"dihedral {i+1} {j+1} {k+1} {l+1} {v:.4f}\n")
            kw["constraints"] = cons
            kw["enforce"] = 0.1
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            import logging
            logging.getLogger("geometric").setLevel(logging.ERROR)
            prog = geometric.optimize.run_optimizer(**kw)
        finally:
            os.chdir(cwd)
    return np.array(prog.xyzs[-1]), float(prog.qm_energies[-1])


def dft_sp(symbols, xyz_ang, xc="b3lyp", basis="def2-tzvp", disp="d3bj", threads=2, grid=3, solvent_eps=None):
    """DF-RKS single point. Returns dict(e_tot, e_disp, converged)."""
    from pyscf import dft, gto, lib

    lib.num_threads(threads)
    mol = gto.M(atom=[(s, tuple(x)) for s, x in zip(symbols, xyz_ang)], basis=basis, unit="Angstrom", verbose=0)
    mf = dft.RKS(mol, xc=xc).density_fit()
    if solvent_eps:  # ddCOSMO continuum, gas-phase geometry
        mf = mf.ddCOSMO()
        mf.with_solvent.eps = float(solvent_eps)
    mf.grids.level = grid
    mf.conv_tol = 1e-9
    if disp:
        mf.disp = disp
    e = mf.kernel()
    return dict(e_tot=float(e), e_disp=float(mf.scf_summary.get("dispersion", float("nan"))),
                converged=bool(mf.converged), nbas=int(mol.nao))


def dfmp2_sp(symbols, xyz_ang, basis="def2-tzvp", threads=2):
    from pyscf import gto, lib, scf
    from pyscf.mp import dfmp2

    lib.num_threads(threads)
    mol = gto.M(atom=[(s, tuple(x)) for s, x in zip(symbols, xyz_ang)], basis=basis, unit="Angstrom", verbose=0)
    mf = scf.RHF(mol).density_fit()
    mf.kernel()
    pt = dfmp2.DFMP2(mf)
    pt.kernel()
    return dict(e_tot=float(pt.e_tot), e_hf=float(mf.e_tot), converged=bool(mf.converged))
