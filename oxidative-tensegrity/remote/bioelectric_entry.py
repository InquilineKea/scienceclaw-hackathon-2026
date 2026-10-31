#!/usr/bin/env python3
"""Container entry for run_bioelectric.py on an image with torch + numpy only (no package installs).

scipy is needed only for the tensegrity solves, which are passed in precomputed via --table, so a stub that
raises if called stands in for scipy.optimize.  Usage: python remote/bioelectric_entry.py <run_bioelectric args>
"""
import runpy
import sys
import types
from pathlib import Path

try:
    import scipy.optimize  # noqa: F401
except ImportError:
    def _unavailable(*a, **k):
        raise RuntimeError("scipy is not installed here: pass the tensegrity table with --table")

    opt = types.ModuleType("scipy.optimize")
    opt.minimize = _unavailable
    sp = types.ModuleType("scipy")
    sp.optimize = opt
    sys.modules["scipy"], sys.modules["scipy.optimize"] = sp, opt

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.argv = [str(root / "run_bioelectric.py")] + sys.argv[1:]
runpy.run_path(str(root / "run_bioelectric.py"), run_name="__main__")
