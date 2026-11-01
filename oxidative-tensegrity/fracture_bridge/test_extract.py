"""Unit tests for the fracture scale-bridge adapter (stdlib unittest + numpy).

Run from the oxidative-tensegrity folder:

    python -m fracture_bridge.test_extract
    # or directly:
    python fracture_bridge/test_extract.py

Coverage required by the experiment brief:
  * synthetic triangular cohesive law with KNOWN G_c recovered to numerical
    precision (trapezoid; the peak sits exactly on a sample point so the
    piecewise-linear curve is integrated exactly);
  * peak strength and delta_f extraction;
  * incomplete-curve flag (truncated failure curve);
  * JSON / CSV loading round-trips;
  * multi-realization mean ± sd aggregation;
  * MOOSE template rendering contains the required parameter blocks.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

# allow running both as a module and as a plain script
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from fracture_bridge import extract_cohesive as ec
    from fracture_bridge import moose_template as mt
else:
    from . import extract_cohesive as ec
    from . import moose_template as mt


def triangular_curve(T_max, delta_f, n_up=2000, n_down=2000, tail=1.25):
    """Sample a triangular cohesive law T(delta) with the peak ON a sample point.

    T rises linearly 0 -> T_max at delta_f/2, then falls linearly to 0 at
    delta_f, and stays 0 until delta_f*tail.  Exact analytic values:
    G_c = 0.5 * T_max * delta_f, K0 = T_max / (delta_f/2) = 2*T_max/delta_f.
    """
    d_peak = 0.5 * delta_f
    up = np.linspace(0.0, d_peak, n_up)
    down = np.linspace(d_peak, delta_f, n_down)
    flat = np.linspace(delta_f, delta_f * tail, 20)
    delta = np.concatenate([up, down[1:], flat[1:]])
    traction = np.concatenate(
        [T_max * up / d_peak, T_max * (1.0 - (down[1:] - d_peak) / (delta_f - d_peak)), np.zeros(19)]
    )
    return delta, traction


class TestTriangularLawRecovery(unittest.TestCase):
    def test_known_G_c_recovered_to_numerical_precision(self):
        T_max, delta_f = 1.5e6, 2.0e-5      # physically-flavoured numbers
        G_c_true = 0.5 * T_max * delta_f    # 15 J/m^2
        delta, traction = triangular_curve(T_max, delta_f)
        r = ec.extract_curve(delta, traction, mode="I", source="triangular")
        self.assertFalse(r.incomplete)
        rel = abs(r.G_c - G_c_true) / G_c_true
        self.assertLess(rel, 1e-12, f"G_c off by {rel:.3e}: {r.G_c} vs {G_c_true}")

    def test_peak_and_delta_f_extraction(self):
        T_max, delta_f = 80.0, 0.05
        delta, traction = triangular_curve(T_max, delta_f)
        r = ec.extract_curve(delta, traction, mode="I", source="triangular")
        self.assertAlmostEqual(r.T_max, T_max, delta=T_max * 1e-12)
        self.assertAlmostEqual(r.delta_peak, 0.5 * delta_f, delta=delta_f * 1e-12)
        # decay threshold 2% of T_max -> crossing slightly BEFORE delta_f
        thr = ec.DEFAULT_DECAY_THRESHOLD
        expected_f = delta_f - thr * T_max * (delta_f - delta_f / 2) / T_max
        # linear branch: T = T_max*(1 - (d - dp)/(df - dp)); T = thr*T_max
        #   -> d = dp + (df-dp)(1-thr)
        expected = 0.5 * delta_f + (delta_f - 0.5 * delta_f) * (1.0 - thr)
        self.assertAlmostEqual(expected_f, expected, delta=1e-15)
        assert r.delta_f is not None
        self.assertAlmostEqual(r.delta_f, expected, delta=delta_f * 1e-9)
        # secant stiffness to peak
        self.assertAlmostEqual(r.K0, T_max / (0.5 * delta_f), delta=1e-9)

    def test_delta_f_respects_custom_threshold(self):
        T_max, delta_f = 1.0, 0.1
        delta, traction = triangular_curve(T_max, delta_f)
        for thr in (0.01, 0.05, 0.10):
            r = ec.extract_curve(delta, traction, decay_threshold=thr)
            expected = 0.5 * delta_f + (delta_f - 0.5 * delta_f) * (1.0 - thr)
            assert r.delta_f is not None
            self.assertAlmostEqual(r.delta_f, expected, delta=delta_f * 1e-9)

    def test_negative_traction_tail_does_not_inflate_or_deflate_G_c(self):
        # compression/noise artifacts below zero are clipped for the energy integral
        T_max, delta_f = 1.0, 0.1
        delta, traction = triangular_curve(T_max, delta_f)
        traction = traction.copy()
        traction[-5:] = -0.3
        r = ec.extract_curve(delta, traction)
        self.assertLess(abs(r.G_c - 0.5 * T_max * delta_f), 1e-9)

    def test_consistency_G_c_equals_half_T_max_delta_f(self):
        T_max, delta_f = 3.3, 0.021
        delta, traction = triangular_curve(T_max, delta_f, n_up=101, n_down=101)
        r = ec.extract_curve(delta, traction, decay_threshold=1e-6)
        assert r.delta_f is not None
        # with a nonzero decay threshold the crossing sits slightly before the
        # true failure separation: delta_cross = dp + (df-dp)(1-thr)
        thr = 1e-6
        expected_cross = 0.5 * delta_f + (delta_f - 0.5 * delta_f) * (1.0 - thr)
        self.assertAlmostEqual(r.delta_f, expected_cross, delta=delta_f * 1e-9)
        # the energy integral runs past the crossing to the true zero-traction
        # separation, so the exact triangle relation holds with delta_f itself
        self.assertAlmostEqual(r.G_c, 0.5 * T_max * delta_f, delta=1e-9)


class TestIncompleteCurveFlag(unittest.TestCase):
    def _truncated(self, cut_fraction):
        T_max, delta_f = 1.0, 0.1
        delta, traction = triangular_curve(T_max, delta_f, n_up=500, n_down=500)
        end = delta_f * cut_fraction
        keep = delta <= end
        return delta[keep], traction[keep]

    def test_truncated_decay_branch_is_flagged(self):
        # cut at 70% of delta_f: traction is ~0.6*T_max there >> 2% threshold
        delta, traction = self._truncated(0.70)
        r = ec.extract_curve(delta, traction, source="truncated")
        self.assertTrue(r.incomplete)
        self.assertTrue(r.G_c_lower_bound)
        self.assertIsNone(r.delta_f)
        self.assertIn("exceeds decay threshold", r.reason)

    def test_curve_ending_at_peak_is_flagged(self):
        T_max, delta_f = 1.0, 0.1
        delta, traction = triangular_curve(T_max, delta_f, n_up=400, n_down=400)
        keep = delta <= 0.5 * delta_f
        r = ec.extract_curve(delta[keep], traction[keep], source="at_peak")
        self.assertTrue(r.incomplete)
        self.assertIn("ends at the peak", r.reason)

    def test_complete_curve_is_not_flagged(self):
        T_max, delta_f = 1.0, 0.1
        delta, traction = triangular_curve(T_max, delta_f)
        r = ec.extract_curve(delta, traction)
        self.assertFalse(r.incomplete)
        self.assertFalse(r.G_c_lower_bound)
        self.assertEqual(r.reason, "")

    def test_all_incomplete_curve_numbers_marked_lower_bound(self):
        delta, traction = self._truncated(0.8)
        r = ec.extract_curve(delta, traction)
        d = r.as_dict()
        self.assertTrue(d["incomplete"] and d["G_c_lower_bound"])
        self.assertEqual(d["delta_f"], None)


class TestLoadingAndAggregation(unittest.TestCase):
    def test_json_single_and_bundle_roundtrip(self):
        T_max, delta_f = 2.0, 0.04
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            single = tmp / "seed0.json"
            d0, t0 = triangular_curve(T_max, delta_f, n_up=50, n_down=50)
            single.write_text(json.dumps({
                "schema": ec.CURVE_SCHEMA, "condition": "c", "mode": "I",
                "realization": 0, "units": {"delta": "m", "traction": "Pa"},
                "delta": list(d0), "traction": list(t0),
            }))
            bundle = tmp / "bundle.json"
            entries = []
            for seed, scale in [(1, 1.1), (2, 0.9)]:
                dd, tt = triangular_curve(scale * T_max, delta_f, n_up=50, n_down=50)
                entries.append({"mode": "I", "realization": seed,
                                "delta": list(dd), "traction": list(tt)})
            bundle.write_text(json.dumps({
                "schema": ec.BUNDLE_SCHEMA, "condition": "c", "realizations": entries}))

            curves = ec.load_realizations(single) + ec.load_realizations(bundle)
            self.assertEqual(len(curves), 3)
            self.assertEqual([c["realization"] for c in curves], [0, 1, 2])

            results = [ec.extract_curve(c["delta"], c["traction"], mode=c["mode"],
                                        realization=c["realization"]) for c in curves]
            summ = ec.aggregate(results, label="c")
            self.assertEqual(summ.n_realizations, 3)
            self.assertEqual(summ.n_complete, 3)
            self.assertTrue(summ.all_complete)

            # analytic ground truth per realization
            true_G = [0.5 * 2.0 * delta_f, 0.5 * 2.2 * delta_f, 0.5 * 1.8 * delta_f]
            for res, g in zip(results, true_G):
                self.assertAlmostEqual(res.G_c, g, delta=g * 1e-6)
            mean = sum(true_G) / 3
            sd = math.sqrt(sum((g - mean) ** 2 for g in true_G) / 2)  # ddof=1
            self.assertAlmostEqual(summ.G_c_mean, mean, delta=mean * 1e-6)
            self.assertAlmostEqual(summ.G_c_sd, sd, delta=sd * 1e-6)

    def test_csv_single_and_long_format_roundtrip(self):
        T_max, delta_f = 1.0, 0.05
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            single = tmp / "one.csv"
            delta, traction = triangular_curve(T_max, delta_f, n_up=40, n_down=40)
            single.write_text("delta,traction\n" + "\n".join(
                f"{d:.8g},{t:.8g}" for d, t in zip(delta, traction)))
            long = tmp / "many.csv"
            rows = ["realization,mode,delta,traction"]
            for seed, scale in [(0, 1.0), (1, 1.2)]:
                d2, t2 = triangular_curve(scale * T_max, delta_f, n_up=40, n_down=40)
                for d, t in zip(d2, t2):
                    rows.append(f"{seed},I,{d:.8g},{t:.8g}")
            long.write_text("\n".join(rows))

            single_curves = ec.load_realizations(single)
            long_curves = ec.load_realizations(long)
            self.assertEqual(len(single_curves), 1)
            self.assertEqual(len(long_curves), 2)
            r = ec.extract_curve(single_curves[0]["delta"],
                                 single_curves[0]["traction"], min_points=3)
            # CSV text is written with 8 significant digits, so the sampled law
            # is linear only to ~1e-8; recovery is exact to that rounding.
            self.assertAlmostEqual(r.G_c, 0.5 * T_max * delta_f, delta=1e-10)
            self.assertAlmostEqual(r.T_max, T_max, delta=1e-12)

            # long-format CSV grouping gives both realizations back
            modes = {c["realization"] for c in long_curves}
            self.assertEqual(modes, {"0", "1"})

    def test_malformed_inputs_raise(self):
        with self.assertRaises(ValueError):
            ec.extract_curve([0, 1, 2], [1.0, 1.0], min_points=3)
        with self.assertRaises(ValueError):
            ec.extract_curve([0, 1, 2], [1.0, 2.0, 3.0, 4.0], min_points=3)
        with self.assertRaises(ValueError):
            # duplicate delta value -> not strictly increasing
            ec.extract_curve([0.0, 1.0, 1.0, 2.0], [0.0, 1.0, 0.5, 0.0], min_points=3)
        with self.assertRaises(ValueError):
            ec.extract_curve(np.linspace(0, 1, 10), np.linspace(0, 1, 10) * 0.0 - 1)
        with self.assertRaises(ValueError):
            ec.extract_curve(np.linspace(0, 1, 10), np.linspace(0, 1, 10),
                             decay_threshold=1.5)

    def test_aggregate_rejects_mixed_modes(self):
        r1 = ec.extract_curve(*triangular_curve(1.0, 0.1), mode="I")
        r2 = ec.extract_curve(*triangular_curve(1.0, 0.1), mode="II")
        with self.assertRaises(ValueError):
            ec.aggregate([r1, r2])
        by_mode = ec.aggregate_by_mode([r1, r2], label="mix")
        self.assertEqual(set(by_mode), {"I", "II"})

    def test_incomplete_realization_counted_in_summary(self):
        results = [
            ec.extract_curve(*triangular_curve(1.0, 0.1), source="ok"),
            ec.extract_curve(*triangular_curve(1.0, 0.1), source="bad"),
        ]
        # truncate the second one
        d, t = triangular_curve(1.0, 0.1)
        keep = d <= 0.075
        results[1] = ec.extract_curve(d[keep], t[keep], source="bad")
        summ = ec.aggregate(results, label="mixed")
        self.assertEqual(summ.n_incomplete, 1)
        self.assertEqual(summ.n_complete, 1)
        self.assertFalse(summ.all_complete)
        self.assertEqual(summ.incomplete_sources, ["bad"])
        self.assertIn("1 complete", summ.delta_f_note)


class TestMooseTemplate(unittest.TestCase):
    def _summaries(self, n=3):
        results = [
            ec.extract_curve(*triangular_curve(1.5e6 * (1 + 0.05 * i), 2e-5),
                             mode="I", source=f"r{i}", realization=i)
            for i in range(n)
        ]
        sI = ec.aggregate(results, label="cond")
        results2 = [
            ec.extract_curve(*triangular_curve(1.0e6 * (1 + 0.05 * i), 3e-5),
                             mode="II", source=f"s{i}", realization=i)
            for i in range(n)
        ]
        sII = ec.aggregate(results2, label="cond")
        return sI, sII

    def test_template_contains_required_blocks_and_numbers(self):
        sI, sII = self._summaries()
        text = mt.render_moose_czm_input("healthy-z3.5", sI, sII)
        for marker in mt.REQUIRED_MARKERS:
            self.assertIn(marker, text)
        self.assertIn("healthy-z3.5", text)
        self.assertIn(f"G_cI = {mt._fmt(sI.G_c_mean)}", text)
        self.assertIn(f"G_cII = {mt._fmt(sII.G_c_mean)}", text)
        self.assertIn(f"normal_strength = {mt._fmt(sI.T_max_mean)}", text)
        self.assertIn(f"shear_strength = {mt._fmt(sII.T_max_mean)}", text)
        self.assertIn(f"normal_stiffness = {mt._fmt(sI.K0_mean)}", text)
        self.assertIn(f"shear_stiffness = {mt._fmt(sII.K0_mean)}", text)
        # uncertainty is carried: sd values quoted in the provenance header
        self.assertIn(f"± {mt._fmt(sI.G_c_sd)}", text)
        # security-review guard
        self.assertIn("DO NOT RUN", text)
        self.assertIn("PLACEHOLDER", text)

    def test_template_mode_I_only(self):
        sI, _ = self._summaries()
        text = mt.render_moose_czm_input("cond", sI, None)
        self.assertIn("G_cI", text)
        self.assertNotIn("G_cII =", text.replace("G_cII / G_cI", ""))
        self.assertIn("UNAVAILABLE", text)  # mixed-mode ratio missing

    def test_template_flags_incomplete_condition(self):
        d, t = triangular_curve(1.0e6, 2e-5)
        keep = d <= 0.6 * 2e-5
        bad = ec.extract_curve(d[keep], t[keep], source="trunc")
        sI = ec.aggregate([bad], label="badcond")
        text = mt.render_moose_czm_input("badcond", sI, None)
        self.assertIn("INCOMPLETE", text)
        self.assertIn("LOWER BOUND", text)

    def test_template_requires_at_least_one_summary(self):
        with self.assertRaises(ValueError):
            mt.render_moose_czm_input("cond", None, None)

    def test_normalized_table_render(self):
        d, t = triangular_curve(1.0, 0.1)
        r = ec.extract_curve(d, t)
        table = mt.render_normalized_curve_table(r)
        rows = [line.split(",") for line in table.strip().splitlines()]
        self.assertEqual(rows[0], ["normalized_delta", "normalized_traction"])
        xs = np.array([float(a) for a, _ in rows[1:]])
        ys = np.array([float(b) for _, b in rows[1:]])
        self.assertEqual(xs[0], 0.0)
        self.assertLessEqual(xs.max(), 1.2)
        self.assertAlmostEqual(ys.max(), 1.0, places=6)
        with self.assertRaises(ValueError):
            d2, t2 = triangular_curve(1.0, 0.1)
            keep = d2 <= 0.07
            mt.render_normalized_curve_table(
                ec.extract_curve(d2[keep], t2[keep]))  # incomplete


if __name__ == "__main__":
    unittest.main(verbosity=2)
