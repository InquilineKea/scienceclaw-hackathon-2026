# Minimal experiment publication contract v1

A finished experiment should emit a bounded publication directory without giving the publishing process simulation credentials. The simulation runner produces files; a separate reviewer/publisher decides whether to expose them.

1. **Identity:** stable experiment ID, date, status (completed / partial / failed), model dimensions and protocol, dimensionless or physical units, article URL, pinned source revisions and any patches.
2. **Design:** paired/blocking identifiers, seeds, independent variables, fixed controls, sample counts and parameter ranges. Distinguish network organization from constitutive or interaction changes.
3. **Evidence:** complete counts, explicit failure records and gate outcomes. A failed pilot can still produce a publishable record; it must not produce an apparently successful comparison.
4. **Data:** machine-readable curve arrays and state geometry, download summaries, source-data digests and an explicit display subset. Save full numerical precision and avoid silently filling missing or nonconverged values.
5. **Integrity:** relative allowlisted paths, bytes and SHA-256 for each data artifact. Exclude credentials, account metadata, unrelated files and raw personal data. Hashes establish identity, not biological validity.
6. **Interpretation:** measured result versus simulation versus hypothesis, numerical validation boundary, unresolved effects and known model omissions.
7. **Views:** ordinary narrative link plus a static interactive companion. A later 3D export must specify coordinate units, topology/bond meaning, periodic geometry, state/strain, scientific versus decorative geometry, source hash and license before external upload.

The adapter in `tools/export.py` implements this pattern for one already-audited fiber dataset. Other experiments need an adapter to this contract, rather than assuming identical input schemas. Source schemas should be versioned and verified before export. Automatic article publication is deliberately a separate step from artifact generation.

## Future compute service: deferred, disabled

A later job service should use a queue and allowlisted models, authenticated submission, hard per-job cost/runtime/size limits, an account-wide budget, concurrency limits and a task-scoped cleanup policy. Browser controls must show clearly when a user is requesting a new computation and report completion/failure separately from saved data. Never embed cloud credentials in a static companion. This prototype has no compute endpoint, no public job submission and no scheduled cloud work.
