# Automatic upload boundary and security review

31 October 2026. The user explicitly requested automatic publication of completed scientific runs to InquilineKea/scienceclaw-hackathon-2026. The uploader is original Python standard-library code. It invokes the already installed Git and GitHub CLI, installs nothing, and executes no fetched repository content or hooks.

| Risk | Severity | Control |
|---|---|---|
| Publishing unrelated files or credentials to a public repository | High | Only a completed run with an exact, verified manifest is accepted. Extra files, symlinks, sensitive paths and recognizable credential patterns are rejected. Runtime children receive a cleared environment. Authentication is used only by the trusted host uploader after computation. |
| Replacing existing data | High | Existing destination contents must match exactly for an idempotent success. A mismatch aborts. New content is added through Git tree objects. No force-push, deletion, checkout, merge script or repository hook is used. |
| Concurrent repository changes | Moderate | Every attempt reads the current main tree. A rejected push retries against its new parent and rechecks the destination. Other paths are preserved. |
| Incomplete output or files modified while publishing | High | Completion marker, complete file list, byte sizes, SHA-256 hashes and model/result identity are checked before bytes enter Git. Upload operates on those checked in-memory bytes. Remote Git blob hashes are checked afterward. |
| Connection/authentication or size failures | Moderate | Local completed data remain intact and the upload is pending. Receipts live outside the frozen run. A retry monitor can retry without rerunning science. Direct Git uploads reject files above 95 MiB rather than silently omit them. |

Inspection covered the new uploader/runner changes, Git plumbing commands and environment handling. Tests use disposable local repositories with no network or credentials and cover idempotence, collision refusal, concurrent commits, manifest changes, extra files, secret-like strings and symlinks. A live integration check uses the user's existing GitHub session only; no pasted credential is read or reused.

The upload scanner is a bounded guard, not proof of absence of private content or unknown credential formats. It is intended for the isolated scientific output directories produced by these workflows, not arbitrary personal folders. Existing Git/GitHub CLI binaries and the OS authentication store remain trusted infrastructure; they were not independently supply-chain re-audited. No GitHub credentials are mounted into a scientific container or copied to a remote machine by this change.

Existing remote molecular runtime code and dependencies are not executed by this update. Future remote execution follows the user's current policy: review and report findings first, isolate and protect credentials, and stay within the authorized task and spending scope. Local third-party execution still requires the user's separate approval after review.
