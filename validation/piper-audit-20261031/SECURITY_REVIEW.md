# Security review and execution gate

Scope: six-case dependency-free JavaScript reproduction pilot only. The four prepared Python source fixes have been parsed as data, not imported or tested.

Inspected the complete 251-line atlas model.js, existing audit.js and run-guard.js, candidate Python default arguments and plotting callback, and relevant driver profiles/documentation. No repository installation/build or package script is required for this pilot. The model has no imports, network, file access, process launch, dynamic evaluation or environment reads. The new harness imports only that copied model and Node standard-library filesystem, path and crypto. It reads copied baseline data, checks the model SHA-256 and writes exclusively to a newly created results directory.

Findings:
- LOW security / MEDIUM correctness: shared dataclass defaults in cell.py and physio.py can leak caller mutations between calls/instances. No evidence yet that historical numerical runs were affected. Prepared per-call construction preserves explicit caller-supplied parameter objects.
- LOW security / LOW present correctness: plot.py captures loop state, but animation saving completes synchronously within the loop. Prepared explicit bindings prevent future delayed callbacks selecting later state; this is not evidence that existing GIFs are wrong.
- MEDIUM execution resource risk: nonlinear solvers can run slowly or fail convergence. Proposed pilot limit is 120 seconds, CPU only, six cases, no new packages or cloud spending.
- MEDIUM supply-chain uncertainty: the preinstalled Node executable and system libraries have not been independently rebuilt or signature-verified here. No npm dependencies will be loaded or installed. Repository-wide lint counts and the full reconstructed Piper report are not available in the pasted summary and are not treated as verified defect counts.
- Network-capable review helper inspect-image.py invokes curl at module import; it is explicitly excluded from execution. Its empty-list default was hardened statically.

Required isolation for execution: copied model/harness/baseline only; macOS sandbox profile denies network and access to user files/credentials, allows the exact Node executable and required system libraries, and permits writes only within a new disposable run directory. No repository package scripts, uploaders, swarms, Python scientific dependencies or credential helpers will run. Review the final runner/profile before execution. Preserve logs, configurations, input hashes, failures and outputs; no frozen folder will be modified.

This review found no malicious behavior in the bounded model source. It does not establish safety of the rest of the repository or verify biological validity. User approval is required before local repository-code execution under /Users/simfish/.codex/AGENTS.md.

