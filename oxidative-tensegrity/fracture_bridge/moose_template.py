"""Render a MOOSE cohesive-zone input-parameter TEMPLATE from extracted values.

This module ONLY generates text. It never runs MOOSE (MOOSE is not installed on
this machine and needs a separate security review first — see AGENTS.md). The
output is a parameter template in MOOSE input syntax, not a verified input file:
keyword names follow the MOOSE Solid Mechanics CZM action family
(``DomainBoundaryCohesiveZone`` mesh generator + ``CohesiveZone`` action), and
the header instructs the MOOSE user to check every keyword against the exact
MOOSE version approved by the security review.

Usage::

    from fracture_bridge.extract_cohesive import extract_paths
    from fracture_bridge.moose_template import render_moose_czm_input

    summaries = extract_paths(["condA_modeI_seed*.json"], label="condA")
    text = render_moose_czm_input("condA", summaries.get("I"), summaries.get("II"))
    open("condA_czm_template.i", "w").write(text)

CLI::

    python -m fracture_bridge.moose_template SUMMARY.json --condition condA \
        [--units "SI (Pa, m, J/m^2)"] -o condA_czm_template.i

where SUMMARY.json is the JSON emitted by ``extract_cohesive.py --json``
(a dict mode -> ConditionSummary.as_dict(), keys "I" and optionally "II").
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HEADER_WARNING = """\
# =========================================================================
# MOOSE cohesive-zone input-parameter TEMPLATE  --  NOT A VERIFIED INPUT FILE
#
# DO NOT RUN until the MOOSE security review is complete (repo rule, AGENTS.md).
# Nothing in fracture_bridge/ executes or installs MOOSE; this file only carries
# the physics parameters the tissue-scale model needs, in MOOSE input syntax.
#
# CHECK KEYWORDS: blocks below follow the MOOSE Solid Mechanics cohesive-zone
# interface (DomainBoundaryCohesiveZone mesh generator, CohesiveZone action,
# PWL / triangular cohesive-law materials). Parameter names DRIFT between MOOSE
# versions. Before running, diff every keyword against the header files of the
# approved MOOSE checkout (modules/solid_mechanics).
# =========================================================================
"""

# Required topics every rendered template must cover (checked by unit tests).
# Shear markers are only required when mode-II data is supplied.
CORE_MARKERS = (
    "DomainBoundaryCohesiveZone",
    "CohesiveZone",
    "G_cI",
    "normal_stiffness",
    "PLACEHOLDER_BULK",
)
SHEAR_MARKERS = (
    "shear_stiffness",
    "G_cII",
    "shear_strength",
)
REQUIRED_MARKERS = CORE_MARKERS + SHEAR_MARKERS  # kept for external consumers


def _fmt(x, digits=6):
    if x is None:
        return "UNAVAILABLE"
    if x == 0:
        return "0.0"
    if abs(x) >= 1e-4 and abs(x) < 1e6:
        return f"{x:.{digits}g}"
    return f"{x:.{digits}e}".replace("e+0", "e+").replace("e-0", "e-")


def _stats_line(name, summary, key):
    if summary is None:
        return f"#   {name}: no data (mode absent from input)"
    s = summary.as_dict()[key]
    return f"#   {name} = {_fmt(s['mean'])} ± {_fmt(s['sd'])} (sd, n={summary.n_realizations} realizations)"


def render_moose_czm_input(
    condition_label,
    summary_I,
    summary_II=None,
    *,
    dimension=3,
    boundary_name="CRACK_INTERFACE",
    mesh_file="notch_specimen.e",
    units_note="UNITS NOT YET PHYSICAL — see fracture_bridge/README.md calibration section",
    include_bulk_placeholder=True,
):
    """Render the MOOSE CZM parameter template text for one condition.

    ``summary_I`` / ``summary_II`` are ConditionSummary objects (mode I = normal
    opening, mode II = shear) from fracture_bridge.extract_cohesive.aggregate.
    At least mode I is required. All extracted numbers enter as mean ± sd over
    realizations; the MOOSE user decides how to propagate the sd (worst case,
    interval runs, or stochastic sampling).
    """
    if summary_I is None and summary_II is None:
        raise ValueError("need at least one ConditionSummary (mode I and/or II)")

    displacements = "disp_x disp_y disp_z" if dimension == 3 else "disp_x disp_y"

    if summary_I is not None and not summary_I.all_complete:
        warn_I = (
            "#   *** WARNING: %d of %d mode-I realizations are INCOMPLETE (traction\n"
            "#       not decayed at max delta). G_cI below is a LOWER BOUND. Re-run the\n"
            "#       network model with larger max crack opening before using it. ***"
            % (summary_I.n_incomplete, summary_I.n_realizations)
        )
    else:
        warn_I = "#   mode-I: all realizations complete."
    if summary_II is not None and not summary_II.all_complete:
        warn_II = (
            "#   *** WARNING: %d of %d mode-II realizations are INCOMPLETE — G_cII is\n"
            "#       a LOWER BOUND. ***" % (summary_II.n_incomplete, summary_II.n_realizations)
        )
    else:
        warn_II = "#   mode-II: all realizations complete."

    def val(summary, key_mean):
        if summary is None:
            return None
        return summary.as_dict()[key_mean]["mean"]

    G_cI = val(summary_I, "G_c")
    Tn_max = val(summary_I, "T_max")
    dn_peak = val(summary_I, "delta_peak")
    dfn = val(summary_I, "delta_f")
    Kn = val(summary_I, "K0")
    G_cII = val(summary_II, "G_c")
    Tt_max = val(summary_II, "T_max")
    dt_peak = val(summary_II, "delta_peak")
    dft = val(summary_II, "delta_f")
    Kt = val(summary_II, "K0")

    # Mixed-mode ratio (only meaningful when both modes present).
    if G_cI and G_cII:
        mixed_line = f"#   G_cII / G_cI = {_fmt(G_cII / G_cI)} (mixed-mode fracture ratio)"
    else:
        mixed_line = "#   G_cII / G_cI: UNAVAILABLE (mode-II data absent)"

    bulk_block = ""
    if include_bulk_placeholder:
        bulk_block = f"""
# ---- Bulk material: NONLINEAR ANISOTROPIC VISCOELASTIC CALIBRATION ----
# The CZM law above only describes the crack plane. The surrounding tissue
# bulk must come from the lower scales of the fracture pipeline:
#   * fibril scale (LAMMPS, remote/lammps/*.in): G'(w), G''(w) -> Prony
#     relaxation spectrum (g_i, k_i, tau_i);
#   * fiber network (oxt, other agent): modulus, anisotropy (fiber
#     orientation tensor / orientation distribution), damage-free response;
#   * physical calibration: convert dimensionless network/LAMMPS output to
#     Pa and m using the length/force/thickness scales in README.md.
# Everything below marked PLACEHOLDER must be filled by that calibration.
  [./bulk_matrix]
    type = PLACEHOLDER_BULK_nonlinear_anisotropic_viscoelastic
    # --- elasticity (nonlinear, large strain) ---
    # candidate base laws to evaluate at review time: neo-Hookean /
    # Mooney-Rivlin hyperelastic; REQUIRED inputs:
    Youngs_modulus = PLACEHOLDER_E          # [Pa] from network G' x thickness
    Poissons_ratio = PLACEHOLDER_nu
    large_kinematics = true
    # --- anisotropy (fiber-reinforced) ---
    # candidate: fiber-direction / orthotropic term with orientation tensor A
    fiber_orientation_tensor = PLACEHOLDER_A_11_A_12_A_13_A_22_A_23_A_33
    fiber_stiffness = PLACEHOLDER_E_f        # [Pa] fibril-scale axial modulus
    fiber_direction = 'PLACEHOLDER_unit_vector'
    # --- viscoelasticity (Prony) ---
    # Prony series fitted to fibril G'(w), G''(w) and network relaxation:
    prony_moduli = 'PLACEHOLDER_g1 PLACEHOLDER_g2 PLACEHOLDER_g3'
    prony_times = 'PLACEHOLDER_tau1 PLACEHOLDER_tau2 PLACEHOLDER_tau3'
    # --- mesh coupling ---
    displacements = '{displacements}'
  [../]
"""

    lines = []
    add = lines.append
    add(HEADER_WARNING)
    add(f"# Condition: {condition_label}")
    add(f"# Units: {units_note}")
    add("#")
    add("# Cohesive-zone parameters extracted by fracture_bridge/extract_cohesive.py")
    add("# from notched-network traction-separation curves (mean ± sd over realizations):")
    add(_stats_line("G_cI   [energy/area]", summary_I, "G_c"))
    add(_stats_line("Tn_max [force/area]", summary_I, "T_max"))
    add(_stats_line("delta_n,peak [length]", summary_I, "delta_peak"))
    add(_stats_line("delta_n,f    [length]", summary_I, "delta_f"))
    add(_stats_line("K_n     [Pa/m]", summary_I, "K0"))
    if summary_II is not None:
        add(_stats_line("G_cII  [energy/area]", summary_II, "G_c"))
        add(_stats_line("Tt_max [force/area]", summary_II, "T_max"))
        add(_stats_line("delta_t,peak [length]", summary_II, "delta_peak"))
        add(_stats_line("delta_t,f    [length]", summary_II, "delta_f"))
        add(_stats_line("K_t     [Pa/m]", summary_II, "K0"))
    add(mixed_line)
    add(warn_I)
    if summary_II is not None:
        add(warn_II)
    add("")
    add("# Consistency check (triangular law): G_c = 0.5 * T_max * delta_f.")
    if Tn_max and dfn:
        add(
            f"#   mode I : 0.5*{Tn_max:.6g}*{dfn:.6g} = {0.5 * Tn_max * dfn:.6g} vs G_cI = {G_cI:.6g}"
        )
    if Tt_max and dft:
        add(
            f"#   mode II: 0.5*{Tt_max:.6g}*{dft:.6g} = {0.5 * Tt_max * dft:.6g} vs G_cII = {G_cII:.6g}"
        )
    add("")
    add("[Mesh]")
    add("  # Insert cohesive-zone interface elements on the controlled notch plane.")
    add("  [./czm_interface]")
    add("    type = DomainBoundaryCohesiveZone")
    add(f"    boundary = '{boundary_name}'")
    add(f"    # input = '{mesh_file}'   # notched specimen mesh (controlled-notch first; see README)")
    add("    # NOTE: check this block against the approved MOOSE version's")
    add("    # modules/solid_mechanics mesh generators before running.")
    add("  [../]")
    add("[]")
    add("")
    add("[GlobalParams]")
    add(f"    displacements = '{displacements}'")
    add("[]")
    add("")
    add("# CZM action: assembles interface kernels + cohesive material on the crack surface.")
    add("[CohesiveZone]")
    add("  [./interface]")
    add(f"    boundary = '{boundary_name}'")
    add("    cohesive_law = 'PWL'          # piece-wise-linear: can carry the raw network T(delta) shape")
    add(f"    displacements = '{displacements}'")
    add("    large_kinematics = true       # collagen tissue works at large strain")
    add("  [../]")
    add("[]")
    add("")
    add("# ---- Cohesive law parameters ----")
    add("# Option A (faithful): piece-wise-linear tables of the normalized network")
    add("# curve delta/delta_f vs T/T_max. Export per condition with")
    add("# extract_cohesive.py (one table per mode) and point the material at them.")
    add("[Materials]")
    add("  [./cohesive_pwl]")
    add("    type = PWL")
    add(f"    boundary = '{boundary_name}'")
    add("    normal_table = 'PLACEHOLDER_norm_T_delta_modeI.csv'   # delta_n/delta_n,f vs T_n/Tn_max")
    if summary_II is not None:
        add("    shear_table  = 'PLACEHOLDER_norm_T_delta_modeII.csv'")
    add("    # CHECK the table-parameter keyword names in the approved MOOSE version.")
    add("  [../]")
    add("")
    add("  # Option B (analytic): triangular cohesive law, parameters from the adapter.")
    add("  # For a triangular law G_c = 0.5 * T_max * delta_f, so the three numbers")
    add("  # below are not independent; MOOSE variants that take (T_max, delta_f)")
    add("  # or (T_max, G_c) should be given the pair quoted here.")
    add("  [./cohesive_triangular]")
    add("    type = PLACEHOLDER_TRIANGLE_CZM_CLASS          # e.g. TriangleCZM-family; verify name")
    add(f"    boundary = '{boundary_name}'")
    add(f"    G_cI = {_fmt(G_cI)}                # mode-I energy release rate  [energy/area]")
    add(f"    normal_strength = {_fmt(Tn_max)}         # Tn_max [force/area]")
    add(f"    normal_stiffness = {_fmt(Kn)}         # K_n [Pa/m]  (= Tn_max / delta_n,peak)")
    if summary_II is not None:
        add(f"    G_cII = {_fmt(G_cII)}                # mode-II energy release rate [energy/area]")
        add(f"    shear_strength = {_fmt(Tt_max)}        # Tt_max [force/area]")
        add(f"    shear_stiffness = {_fmt(Kt)}        # K_t [Pa/m]  (= Tt_max / delta_t,peak)")
    add("    # delta_n,f and delta_t,f (failure separations) for reference:")
    add(f"    #   delta_n,f = {_fmt(dfn)}   delta_t,f = {_fmt(dft)}")
    add("  [../]")
    add(bulk_block)   # bulk material lives in the SAME [Materials] block
    add("[]")
    add("[BCs]")
    add("  # PLACEHOLDER: specimen grip loading from the tissue-scale experiment protocol.")
    add("  # Mixed-mode loading: prescribe normal and shear displacement components on the")
    add("  # grips; keep the notch plane as the only pre-defined crack path (see README).")
    add("[]")
    add("")
    add("[Executioner]")
    add("  type = Transient")
    add("  solve_type = 'PJFNK'")
    add("  petsc_options_iname = '-pc_type -pc_factor_shift_type'")
    add("  petsc_options_value = 'lu nonzero'")
    add("  dt = PLACEHOLDER_dt          # PLACEHOLDER: choose from K_n and mesh size (stability)")
    add("  dtmin = PLACEHOLDER_dtmin")
    add("  end_time = PLACEHOLDER_end_time")
    add("[]")
    add("")
    add("[Outputs]")
    add("  exodus = true")
    add("  csv = true")
    add("[]")
    add("")
    add("# End of template. Postprocess: J-integral / energy-release-rate comparison")
    add("# against the network-scale G_c is the acceptance test for the bridge.")
    text = "\n".join(lines)

    required = list(CORE_MARKERS) + (list(SHEAR_MARKERS) if summary_II is not None else [])
    missing = [m for m in required if m not in text]
    if missing:
        raise RuntimeError(f"template lost required markers: {missing}")
    return text


def render_normalized_curve_table(result, n_points=200, tail_fraction=1.2):
    """Render a PWL-style normalized table (delta/delta_f vs T/T_max) for one curve.

    Requires a complete CurveResult (delta_f known). Returns CSV text with
    columns ``normalized_delta,normalized_traction``.
    """
    if result.incomplete or result.delta_f is None:
        raise ValueError(f"cannot normalize incomplete curve: {result.source}")
    import numpy as np

    grid = np.linspace(0.0, tail_fraction, n_points)
    # always include the peak node (delta_peak/delta_f) so linear interpolation
    # between samples cannot clip T_max below 1.0 in the table
    peak_node = float(result.delta_peak / result.delta_f)
    grid = np.unique(np.concatenate([grid, [peak_node]]))
    traction = np.clip(result.traction_arr, 0.0, None)
    normalized = np.interp(grid * result.delta_f, result.delta_arr, traction,
                          left=0.0, right=0.0)
    rows = ["normalized_delta,normalized_traction"]
    for d, t in zip(grid, normalized):
        rows.append(f"{d:.8e},{t / result.T_max:.8e}")
    return "\n".join(rows) + "\n"


# --------------------------------------------------------------------------- #
# CLI: build a template from a summary JSON emitted by extract_cohesive.py
# --------------------------------------------------------------------------- #
def _summary_from_dict(mode, payload):
    from fracture_bridge.extract_cohesive import ConditionSummary

    return ConditionSummary(
        label=payload["label"],
        mode=mode,
        n_realizations=payload["n_realizations"],
        n_complete=payload["n_complete"],
        n_incomplete=payload["n_incomplete"],
        G_c_mean=payload["G_c"]["mean"],
        G_c_sd=payload["G_c"]["sd"],
        T_max_mean=payload["T_max"]["mean"],
        T_max_sd=payload["T_max"]["sd"],
        delta_peak_mean=payload["delta_peak"]["mean"],
        delta_peak_sd=payload["delta_peak"]["sd"],
        K0_mean=payload["K0"]["mean"],
        K0_sd=payload["K0"]["sd"],
        delta_f_mean=payload["delta_f"]["mean"],
        delta_f_sd=payload["delta_f"]["sd"],
        all_complete=payload["all_complete"],
        incomplete_sources=payload["incomplete_sources"],
        per_realization=payload["per_realization"],
        delta_f_note=payload["delta_f_note"],
    )


def _cli(argv=None):
    parser = argparse.ArgumentParser(
        prog="moose_template",
        description="Render a MOOSE CZM parameter template from an extraction summary JSON.",
    )
    parser.add_argument("summary_json", help="JSON from extract_cohesive.py --json")
    parser.add_argument("--condition", default="condition", help="condition label for the header")
    parser.add_argument("--units", default="UNITS NOT YET PHYSICAL — see fracture_bridge/README.md")
    parser.add_argument("-o", "--out", default="-", help="output file ('-' = stdout)")
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.summary_json).read_text())
    summary_I = _summary_from_dict("I", payload["I"]) if "I" in payload else None
    summary_II = _summary_from_dict("II", payload["II"]) if "II" in payload else None
    text = render_moose_czm_input(
        args.condition, summary_I, summary_II, units_note=args.units
    )
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text)
        print(f"template written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
