# Source submission review — 1 November 2026

This submission archives reviewed project source and public scientific evidence; it does not execute any of the recovered programs, start a cloud job, deploy a website, install dependencies or change account settings.

## Inspection and checks

- Explicit allowlist packaging selected 202 recovered source/evidence files and added documentation plus a provenance manifest. Raw account/tool responses, chat/model prompts, authentication and cloud connection helpers were excluded.
- All 54 copied Python sources parsed with the standard-library AST parser; all 14 non-vendor JavaScript sources passed Node parsing without module evaluation. JSON syntax and all 202 source-manifest hashes were verified. No solver, MD, adapter, imported package, build system or recovered program was run for this submission.
- Static content scan found no recognized private-key block, GitHub/Google/OpenAI/AWS credential pattern, literal long bearer credential, original user-home path or private LAN address in the staged files. This is a bounded pattern scan and review, not proof that all possible sensitive strings or defects are absent.
- Eleven copies had local workspace/user-home prefixes replaced with `/path/to/...`; original and submitted hashes and modifications are recorded in `SOURCE_MANIFEST.json`. The four public app trees otherwise preserve the already tested public source.
- All 34 byte-identical blobs already in the pinned repository tree are reused where possible. Large original ZIP bundles remain linked to their public hosting rather than being added again.
- No workflow, Git hook, installation script, dependency manifest or automatic execution configuration is added or modified. The repository's existing Pages workflow only reacts to `docs/**` and its own workflow file; this companion namespace does not redeploy the existing apps.

## Material limitations

Historical CPU/MD programs contain Docker/process/filesystem operations and dated run guards; data adapters read original archives and network sources; integration scripts can be non-idempotent. They are preserved as historical source and require fresh review, explicit appropriate authorization and resolved input/runtime dependencies before any future run. An archived approval is never a new authorization. Local path placeholders do not make historical scripts portable.

The complete third-party Martini inputs/force fields and raw trajectories are omitted because of size and unresolved redistribution scope. Upstream components included in public interfaces keep their existing license notices; no new blanket license is asserted. Source hashes and provenance support comparison but do not establish safety, licensing clearance or scientific validation.

Scientific results retain their original gates and failures: no molecular-to-network calibration is inferred from the failed Martini production, short CPU replay or rejected hydrated stiffness transfer. Network sensitivity results remain normalized assumed-law experiments. Static 3D inspection does not perform new molecular dynamics.
