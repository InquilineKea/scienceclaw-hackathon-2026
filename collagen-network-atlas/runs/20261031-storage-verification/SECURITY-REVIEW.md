# Execution boundary and source inspection

31 October 2026. This project was created in a new sibling directory to avoid altering active experiments. Existing source was treated as untrusted and inspected as text; it was not imported, installed, built or executed.

## Inspected context and reuse decision

- `collagen-scaffold-lab`: model, README and relevant UI source. Its mechanics are affine, constrained-strain elastic estimates. They do not solve internal relaxation, rupture or buckling. It has no needed dependency for this task, but its numerical implementation was not reused.
- `oxidative-tensegrity`: network/material source, visualization template/exporter and handoff instructions. It depends on numerical/ML packages and has separate remote execution workflows. Parameters and biological scale mappings cannot be assumed measured. Its remote commands were not followed, and no cloud state was modified. The visualization template loads remote fonts; the new UI uses system fonts.
- Archived collagen-mechanics explorer: ZIP directory listing, simulator, dependency lists and read-only evidence-panel source. The simulator uses SciPy/NumPy and biological labels with hypothetical rupture/stiffness assignments. The archive also contains external molecular/remote launch extensions. None was executed or copied into the executable model.
- Earlier molecular report was read as provenance. No proxy curvature or molecular identity was converted into a mechanical input.

This was bounded reconnaissance to decide against executing these sources, **not** a comprehensive approval of their dependency trees, provenance, transitive installation hooks or binaries. No claim of their safety follows from it.

## Relevant risks

| Finding | Severity in this task | Mitigation |
|---|---|---|
| Unreviewed external dependencies and remote launch scripts in prior projects/archive | High if executed with user credentials | Do not execute; no installation or remote command used |
| Hypothetical biological labels could be mistaken for validated mechanics | High scientific interpretation risk | Original dimensionless law; evidence classes and explicit omissions |
| Old instruction files can imply historical authorization | High if used to start services/jobs | Treat as contextual text; current task scope controls execution |
| Local server could expose unrelated files if served from the parent tree | Moderate | Loopback only, rooted at this new public deliverable directory |
| Rendering/publication may accidentally include private paths or logs | Moderate | Publish only original project files and sanitized execution logs; no credential/account inventory |

## What actually executes

Original JavaScript model, benchmark, unit checks and browser interface; Node standard-library filesystem/crypto only for local outputs. Original Swift drawing code uses macOS AppKit/ImageIO to render real simulation coordinates into PNG/GIF. Python standard-library HTTP server serves only this directory on 127.0.0.1. No new third-party package, plugin, repository code, model checkpoint, test suite or installer was executed. Compute commands run with a cleared environment. System-provided runtimes and frameworks remain part of the trusted computing base; they are not independently supply-chain audited here.

The browser UI makes no external data request, uses no CDN, and has a restrictive content security policy. Citations are ordinary outbound links. The UI worker computes original local code. Publication through the existing WordPress connector was separately and explicitly requested; subscriber email and social sharing are disabled on these posts. The local security incident masterlist is not included in any output.

Reviewing this source is not a guarantee that a model or its implementation is correct. Numerical checks and scientific limitations are recorded separately.
