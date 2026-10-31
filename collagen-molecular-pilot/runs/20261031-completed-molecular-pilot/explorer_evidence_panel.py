"""Read-only molecular evidence panel for the existing Streamlit explorer.

Call render_molecular_evidence(st, Path(__file__).resolve().parent).
It does not write or modify any network stiffness/failure parameter.
"""
import json
from pathlib import Path


def render_molecular_evidence(st, project_root):
    base = Path(project_root) / "outputs" / "brev_fragment_pilot"
    st.subheader("Brev molecular geometry evidence")
    st.caption("NVIDIA ALCHEMI Toolkit FIRE2 with MACE-OFF23. Isolated neutral fragments; no reactions, solvent, or tissue calibration.")
    p = base / "results.json"
    if not p.exists():
        st.info("No completed geometry result is attached to this explorer.")
        return
    result = json.loads(p.read_text())
    provenance = json.loads((base / "provenance.json").read_text())
    rows = result.get("results", [])
    if not rows:
        st.warning("Result file contains no molecular structures.")
        return
    passed = sum(bool(x.get("validation_pass")) for x in rows)
    a, b, c = st.columns(3)
    a.metric("Passed geometry checks", f"{passed}/{len(rows)}")
    b.metric("Relaxation time", f"{result['elapsed_seconds']:.1f} s")
    c.metric("GPU", provenance.get("gpu", "Unknown"))
    st.dataframe([{
        "Structure": r["structure_id"], "Atoms": r["atom_count"],
        "Energy change (eV)": r["energy_change_eV"],
        "Maximum force (eV/Å)": r["fmax_eV_A"],
        "Converged": r["converged"], "Geometry checks": r["geometry_sanity_pass"],
        "Relative conformer energy (eV)": r["relative_energy_within_same_compound_eV"],
    } for r in rows], hide_index=True, use_container_width=True)
    st.warning("These calculations do not determine collagen stiffness, rupture force, or reaction rates. The network model's parameters remain assumptions. Compare relative energies only within the same molecule.")
    st.caption("The crosslink-related systems are an amide motif and a truncated dityrosine biaryl core. They are not full glucosepane, pyridinoline, 4-HNE adducts, or crosslinked collagen helices.")
    chosen = st.selectbox("Relaxed fragment coordinates", [r["structure_id"] for r in rows])
    path = base / (chosen + "_relaxed.sdf")
    if path.exists():
        st.download_button("Download relaxed SDF", path.read_bytes(), path.name, "chemical/x-mdl-sdfile")
    st.download_button("Download molecular result JSON", p.read_text(), "brev_fragment_results.json", "application/json")
    with st.expander("Execution and model provenance"):
        st.json(provenance)

