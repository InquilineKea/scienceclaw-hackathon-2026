#!/usr/bin/env python3
"""Backfill experiments/registry.db with the pre-registry experiments recorded in AGENTS.md.

Run from the repo folder:  python experiments/backfill_registry.py
Idempotent: existing ids are skipped. Uses registry.py's transition API so the
verify-rule (verifier must be a DIFFERENT calculation than params['calculation'])
is enforced even on backfilled rows.

Honesty rules used for validation_status (evidence in AGENTS.md, per-experiment
reports and HYPOTHESES_EWALD.md, 2026-10-31):
  independently_verified — a genuinely different calculation/solver reproduced
    the headline quantity (B1 peak force via PM7; junction-angle H100 force-CV
    via the independent CPU implementation; 3D stresses via finite-difference
    + CPU/GPU energy cross-checks).
  refuted — the recorded evidence contradicts the hypothesis (setpoint_vs_scar).
  unvalidated — everything else: internal replications (more seeds / sizes /
    dt-halving / hardware of the same solver) or agent agreement do NOT count
    as independent verification.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry  # noqa: E402

BACKFILL_NOTE = ("Backfilled 2026-10-31 from AGENTS.md / per-experiment reports; "
                 "code_version (git sha at run time) was not recorded for pre-registry runs.")

# (add-kwargs, action, action-kwargs)  action: None | ("verify", ...) | ("refute", ...)
ENTRIES = [
    (
        dict(
            exp_id="cpu32-sweep",
            hypothesis=("Dimensionless linearized fibre-network sweep: how crosslink dose, "
                        "tissue type and connectivity change network, tissue, cell and physio "
                        "outputs (oxt model, README claims)."),
            params={"calculation": "run_sweep.py (oxt fibre-network model, L-BFGS relaxation)",
                    "grid": "16x16 conditions x 4 seeds (values not recorded in AGENTS.md)",
                    "runner": "GCP VM oxt-cpu32, project scienceclaw26bos-3008, 6833 s",
                    "also_ran": "run_gag.py --profile cpu32 (12x12 GAG sweep) on the same VM",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="results/cpu32/",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="phase-map",
            hypothesis=("Phase map of healthy Col I vs connectivity z with LOX locking and AGE "
                        "dose: connected above z~2.4, bending-rigid from ~3.0, stretching-dominated "
                        "above ~3.9, brittle above ~5; AGE dose 1 at matched z raises G 2-3x, "
                        "lowers strain-at-peak 10-35%, shifts the useful window to z 3.2-3.55; "
                        "LOX locking stiffens only below z~4."),
            params={"calculation": "run_phase.py + analyze_phase.py + analyze_fss.py (same oxt solver)",
                    "runs": "W=12 map (4 seeds), 8-seed follow-up, W=16 stiffness check",
                    "note": "8-seed follow-up and W=16 check are same-solver replications, not "
                            "independent verification; the 4-seed 'optimum at z 3.5' did not "
                            "survive 12 seeds. " + BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="results/phase/ (phase_summary.md, fss_summary.md)",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="pm7-tiebreaker",
            hypothesis=("PM7 (MOPAC) semi-empirical cross-check of ALCHEMI crosslink stiffness "
                        "rankings: k_rel disagrees with both MACE models (0.40-0.48) and is "
                        "conformer-dependent; only 'dityrosine stiff, disulfide and TG2 soft' "
                        "is robust; the MLIP scan largely measures conformer slack."),
            params={"calculation": "pm7_crosslinks.py, MOPAC 23.2.5 PM7 (504 optimisations, 0 failed)",
                    "runner": "Brev L4, CPU no-network container (remote/brev_pm7.sh)",
                    "role": "this run IS the independent verifier for b1-alchemi-two-mlip "
                            "(peak force only); no third method has checked PM7 itself",
                    "note": BACKFILL_NOTE},
            seeds=[7], status="done",
            result_location="results/alchemi_brev/crosslink_pm7.json; results/alchemi_brev/crosslink_model_comparison.md",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="b1-alchemi-two-mlip",
            hypothesis=("Converged ALCHEMI crosslink stretch scans with two independent MLIPs "
                        "(MACE-OFF and MACE-MP) rank oxidative crosslinks (dityrosine, sulfilimine, "
                        "HLNL, glucosepane, pentosidine, disulfide, TG2) against the pyridinoline "
                        "reference."),
            params={"calculation": "ALCHEMI two-MLIP stretch scans: MACE-OFF + MACE-MP (alchemi_crosslinks.py)",
                    "alchemi_commit": "84fe8e8fb8fab54863eea8f138722c7ab434966a (user-approved 2026-10-30)",
                    "runner": "Brev L4 (remote/gpu_run.sh)",
                    "known_issues": "normalized stiffness differs 5.60x (HLNL) and 5.77x (sulfilimine) "
                                    "between the two models; boundary minima affect OFF sulfilimine and "
                                    "the MP pyridinoline reference; not fed into the network model",
                    "note": BACKFILL_NOTE},
            seeds=[7], status="done",
            result_location="results/alchemi_brev/crosslink_mace_off.json; results/alchemi_brev/crosslink_mace_mp.json",
        ),
        "verify", dict(
            verifier="PM7 (MOPAC 23.2.5) semi-empirical cross-check",
            method=("PM7 matches both MACE models on PEAK FORCE from the shared seed-7 conformer "
                    "(Spearman 0.95-0.98). k_rel is NOT verified: PM7 k_rel vs MACE 0.40-0.48 and is "
                    "conformer-dependent. Robust across all three methods: dityrosine stiff, disulfide "
                    "and TG2 soft; glucosepane vs pyridinoline, HLNL, pentosidine and sulfilimine remain "
                    "undetermined (see results/alchemi_brev/crosslink_model_comparison.md)."),
            by="backfill from AGENTS.md B1 PM7 check (Claude Code, 2026-10-31)",
        ),
    ),
    (
        dict(
            exp_id="b5-collagen-gag",
            hypothesis=("Collagen-GAG interface vs glycation (H8): MG-H1-Arg is the weakest "
                        "dermatan-sulfate binder and loses contact (minimum pushed from 2.8 A to "
                        "4.0-4.5 A); Arg > Lys; CML-Lys stays bound."),
            params={"calculation": "alchemi_collagen_gag.py, AIMNet2 (aimnet==0.2.5) rigid gas-phase fragments",
                    "runner": "Brev L4, 24 orientations; CPU pilot (Docker, 6 orientations) in results/alchemi_gag/collagen_gag_pilot.json",
                    "caveat": "magnitudes shift ~0.5 eV between CPU and L4 (RDKit conformers differ by "
                              "architecture) — CPU-vs-L4 is not independent verification; contact "
                              "energies, not free energies",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="results/alchemi_gag/collagen_gag_brev_L4.json",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="junction-angle-2d-cpu",
            hypothesis=("Broadening achieved junction-angle SD slightly reduces interface-force CV "
                        "for weak/free angular constraints and increases it for stronger constraints "
                        "(2D high-connectivity scaffold sensitivity result, not isolated angle "
                        "causality or gene-expression validation)."),
            params={"calculation": "experiments/junction-angle-20261031 pilot.py, 36 CPU mechanics cases",
                    "runner": "isolated offline container on existing collagen-md-l40s-20261031",
                    "caveat": "the initial four-seed sign pattern did not survive the later size/seed "
                              "extension (see junction-angle-h100 and H100-RESULTS.md)",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="experiments/junction-angle-20261031/BASELINE_REPORT.md",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="junction-angle-h100",
            hypothesis=("CUDA size/seed sweep of the junction-angle 2D scan (144/144 cases) plus "
                        "8-seed extension: the initial four-seed sign pattern is NOT robust across "
                        "sizes/seeds; mixed small-network signs, positive larger-network mean effects."),
            params={"calculation": "gpu_sweep.py, CUDA on Nebius H100 junction-organoid-h100-20261031",
                    "runs": "144/144 cases accepted, CUDA runtime 13.75 s, container exit 0; "
                            "8-seed/size extension on top",
                    "negative_result": "four-seed sign pattern not robust across size/seeds",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="experiments/junction-angle-20261031/H100-RESULTS.md; experiments/junction-angle-20261031/h100-results/",
        ),
        "verify", dict(
            verifier="independent CPU reference implementation (same model, separate code path)",
            method=("CPU/GPU force-CV agreement within 6.96e-9 on all 36 shared cases — the CUDA "
                    "numerics are verified. This verifies the CALCULATION, not the biological "
                    "generalization: the four-seed sign pattern did not survive the 8-seed/size "
                    "extension, so cite only after reading H100-RESULTS.md."),
            by="backfill from AGENTS.md H100 completion note (Codex, 2026-10-31)",
        ),
    ),
    (
        dict(
            exp_id="junction-angle-3d",
            hypothesis=("3D periodic Voronoi shear grid (z 3.0-4.0, 10 seeds) plus finite "
                        "cavity/anchoring pilot: finite-bending operational onset is not a true "
                        "critical strain; complete-case mean force-CV differences are negative in "
                        "11/12 settings but every setting has mixed seed signs."),
            params={"calculation": "3D periodic Voronoi shear solver (experiments/junction-angle-20261031/three-d), CUDA on H100",
                    "runs": "10 seeds x (21 positive strains + zero); refined 2351/2420 states accepted "
                            "incl. 110 zero controls, 80/110 accepted at 50% shear; cavity pilot 8/8 angle "
                            "pairs matched, 126/144 mechanics accepted (all 18 failures are seed30/parent-z3.2)",
                    "caveat": "compliant anchors are VII-inspired architecture assumptions, not calibrated "
                              "collagen-VII properties; gene directions conditional",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="experiments/junction-angle-20261031/three-d/REPORT.md",
        ),
        "verify", dict(
            verifier="independent CPU/GPU energy cross-check and finite-difference stress check",
            method=("CPU/GPU energy agreement and finite-difference stress vs solver stress both "
                    "passed; low-strain stress changed <=0.00275% on tighter tolerance; 79 remote "
                    "file hashes and archive hash verified."),
            by="backfill from AGENTS.md 3D follow-up note (Codex, 2026-10-31)",
        ),
    ),
    (
        dict(
            exp_id="controlled-geometry",
            hypothesis=("Controlled geometry and spatial signaling: with pairwise geometry-only "
                        "optimization (16/16 matched pairs), broad-minus-narrow mean force CV is "
                        "negative in all six size/lock settings, reversing the prior unmatched "
                        "pilot's direction; YAP/Hill gene-effect signs vary across assumed response "
                        "parameters."),
            params={"calculation": "controlled campaign (campaign.py / campaign_v2.py / mechanics.py), CUDA on H100",
                    "runs": "384 mechanics cases across two campaigns (initial 0/16 geometry pairs, "
                            "follow-up 16/16), all numerically accepted",
                    "caveat": "the follow-up is adaptive geometry-method development, not independent "
                              "replication; mean-force, homogenization, permutation and YAP-off controls "
                              "plus dt-halving validate implementation, not mechanism",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="experiments/junction-angle-20261031/controlled/REPORT.md",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="setpoint-vs-scar",
            hypothesis=("The organoid matrix-feedback loop defends an interior stiffness setpoint "
                        "(tissue memory) rather than accumulating a scar at the stiffness bound "
                        "under AGE-like MMP resistance."),
            params={"calculation": "setpoint_vs_scar.py frozen-radius assay of the oxt organoid gene/LOX/MMP14 loop",
                    "runner": "GCP oxt-cpu32, isolated directory ~/setpoint-scar-20261031",
                    "design": "dose {0,1} x initial matrix factor {0.7,1,1.4} x stiffness pulse "
                              "{1/1.8,1,1.8} x bounds {0.4-2.5, 0.1-10}; 90 d at 0.2 h steps plus a "
                              "360 d slow-relaxation check at 0.4 h",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="results/setpoint_vs_scar/; results/setpoint_vs_scar_360/; SETPOINT_VS_SCAR_20261031.md",
        ),
        "refute", dict(
            reason=("No tested state meets the predeclared setpoint criterion (return to an interior "
                     "target after perturbations in both directions): dose-1 runs hit the imposed "
                     "upper bound in 9/9 conditions with strong positive drive, and widening the bound "
                     "moves the 'scar' plateau to the new bound, proving numerical clipping dominates; "
                     "pulses leave low/mid-start endpoints within 0.001-0.006 and cause no switch; "
                     "native low starts are still slowly drifting at day 360. The tested loop does not "
                     "defend an interior stiffness setpoint."),
            by="backfill from SETPOINT_VS_SCAR_20261031.md (Claude Code, 2026-10-31)",
        ),
    ),
    (
        dict(
            exp_id="bioelectric-ageing",
            hypothesis=("Bioelectric ageing: crosslinking changes membrane-potential spatial "
                        "statistics (Vmem Moran's I, switching patterns) in the multicell/tensegrity "
                        "model, in the direction seen in senescent keratinocytes."),
            params={"calculation": "oxt/bioelectric.py + run_bioelectric.py, pinned PyTorch, no network",
                    "runner": "Nebius H100 bioelectric-ageing-h100-20261031 via Brev, 41 min, disk kept",
                    "negative_results": "Vmem Moran's I RISES with crosslinking (opposite to senescent "
                                        "keratinocytes); 0/108 sets match all four expected signs; spatially "
                                        "correlated stiffness nucleates switching; pattern memory depends on "
                                        "prestress-gated junctions and net restoration is ~0",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="results/bioelectric/gpu/ (SUMMARY.md, DIAGNOSTICS.md)",
        ),
        None, None,
    ),
    (
        dict(
            exp_id="glucosepane-dityrosine-md",
            hypothesis=("Explicit-solvent MD pilots of glucosepane- vs dityrosine-linked collagen "
                        "coupons vs their unlinked controls show distinct local mechanical/stability "
                        "signatures in distinct local collagen contexts."),
            params={"calculation": "Codex MD pipeline: 12 accepted 50-ps linked/control trajectories "
                                   "(600 ps total, 30-ps free tail each), published Amber99 glucosepane "
                                   "and CHARMM/CGenFF DITY parameters, Brev L4 collagen-crosslink-followup-20261031",
                    "scope": "explicitly NOT a cross-chemistry mechanical ranking, full-fibril/B6 "
                             "completion or reaction calculation",
                    "checks": "all dry/wet/runtime/final-readback checks passed; 199 raw-file hashes verified",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location=("swarm/CODEX_CANDIDATE_COMPARISON_20261031.md (full package outside the repo: "
                             "/Users/simfish/Documents/Codex/2026-10-31/https-claude-ai-artifact-xrqknqjnytbutcwtrwpx31-https/outputs/"
                             "collagen-glucosepane-dityrosine-20261031)"),
        ),
        None, None,
    ),
    (
        dict(
            exp_id="topo-opt-nsga2",
            hypothesis=("NSGA-II topology optimization of Col I fibre-network organoid scaffolds "
                        "(7 genes, stiffness band from YAP calibration): no layout beats a plain "
                        "network of the same stiffness on toughness; aligned x-rich layouts with "
                        "sparse crossing locks transmit ~3.5x more bulk strain to the pore "
                        "neighbourhood at matched stiffness; the front is a pilot, not converged."),
            params={"calculation": "topo_opt.py (numpy NSGA-II) + analyze_topo.py on the oxt fibre-network model",
                    "runs": "prototype W=10 (Mac), GA W=12 x 4 generations (oxt-cpu32, 26 workers), "
                            "re-evaluations W=16 and W=12x8 realisations",
                    "negative_results": "GA toughness gains did not survive re-evaluation (rank corr "
                                        "0.19 at W=16, 0.22 with 8 realisations); toughness at fixed "
                                        "stiffness is set by connectivity, not layout; reproducibility is "
                                        "the binding constraint (best designs in band 5-6 of 8 realisations)",
                    "internal_cross_check": "exact Cholesky-solved Hessian linear response matches "
                                            "L-BFGS small_strain_moduli to 1-6% (G, Cx) on W=10 tests — "
                                            "an implementation check, not independent verification of the front",
                    "note": BACKFILL_NOTE},
            seeds=[], status="done",
            result_location="results/topo/ (ga_W12_*, reeval_W12x8_*, reeval_W16_*; TOPO_OPT.md)",
        ),
        None, None,
    ),
]


def main() -> int:
    db = registry.default_db_path()
    conn = registry.connect(db)
    added, skipped = [], []
    for add_kwargs, action, action_kwargs in ENTRIES:
        exp_id = add_kwargs["exp_id"]
        if registry._get_or_none(conn, exp_id) is not None:
            skipped.append(exp_id)
            continue
        add_kwargs.setdefault("code_version", None)  # run-time shas were not recorded
        registry.add_experiment(conn, **add_kwargs)
        if action == "verify":
            registry.verify_experiment(conn, exp_id, **action_kwargs)
        elif action == "refute":
            registry.refute_experiment(conn, exp_id, **action_kwargs)
        added.append(exp_id)
    print(f"DB: {db}")
    print(f"added: {len(added)} {added}")
    print(f"skipped (already present): {len(skipped)} {skipped}")
    counts = {}
    for rec in registry.list_experiments(conn):
        counts[rec["validation_status"]] = counts.get(rec["validation_status"], 0) + 1
    print("validation_status counts:", json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
