# Resume preservation and permission review

2026-10-31. This review inspected the original resume bootstrap, main-loop scheduling change, local resume-state ZIP and amendment provenance. It did not create or change any cloud resource and executed no third-party numerical code.

## Identity and bounded change

The class/function source segments `Model`, `simulate` and `checks` are byte-identical between `cpu-solver-final.py` and `cpu-solver-resume-prepared.py`. Their independently computed source SHA256 values exactly match RESUME_FUNCTION_IDENTITY.json: Model `e849afa9337e7c291bca988a22f7da34ae268722fd6c6db658dfd52c98a91d75`; simulate `dd0b10f247610214b3272d5fa75afb4dd89219b84683fdcf3f64b72b7fed6e80`; checks `d02658263ecf05be06c7dc0b651f0f2469717e59e969d9e9ebfa3c9e4e82e6a2`. Independent AST identity also passes, with its separate normalized hashes recorded. No physical law, force threshold, acceptance gate, step resolution, energy integration, Hessian screen or per-case optimizer changes in the resume.

The scheduling change skips existing final outputs only when status is converged or unresolved, nonempty frames are present and the seed/plane/threshold/pattern/density/step metadata match the requested case. It does not selectively rerun failed-but-final cases. Commissioning is skipped when the verified resume-provenance marker exists; numerical preflight checks still run.

## Resume input preservation

The resume-state ZIP SHA256 independently verifies as `f4c8573194af1a113f4054ac525dd3394478c45ceca4e50c6951219619614929`. It contains 54 final result JSON files, two completed commissioning JSON files and resume-provenance.json. It contains no partial files or directory entries. All 54 original final records currently have status converged. The scheduling logic would also preserve a valid unresolved record if present.

Every one of the 54 final files and two commissioning files is byte-identical to its preserved counterpart in the verified original archive extraction `remote-completed`, whose receipt identifies prior archive SHA256 `1e5608e44409fa08cc3cedf183e27eca84167c827cf4f2e5efa5b877db7b7bf4`. This baseline check is saved in resume-input-preservation-baseline.json. It is not a claim about a resumed archive that has not yet been downloaded.

The bootstrap verifies the original wheel payload SHA, the resume amendment SHA `97fdb44495141e187280dc67032d3ec7fee0a42a9ba40e4276120e9da6518b74` and the resume-state ZIP SHA before execution. Outer amendment entries are restricted to basenames; resumed output paths are restricted to results/, commission/ or the provenance filename and reject absolute/parent traversal paths. Wheel hashes and internal traversal checks are retained.

## Permissions and deadlines

The temporary root and its results/commission directories are assigned UID/GID65534. Old copied files remain readable and are skipped by the worker; new cases can create their own partial and final files in the owned directories. Because the resume ZIP excludes old partial files, there is no root-owned partial checkpoint that would prevent a new task from overwriting its own checkpoint. No personal directories or user credentials are passed in the clean worker environment. The private provider mount remains the artifact transport boundary already described in the runtime review; no stronger kernel network/filesystem isolation is inferred.

The bootstrap now has an independent threading.Timer that kills the worker process group at the explicit absolute deadline, in addition to its periodic archive/elapsed guard and the provider timeout. It retains source, provenance and all preserved/new results in the returned archive. CPU resource limits may terminate an individual very long worker earlier; a partial/missing case must remain visible if that occurs. No guarantee of 160 scientifically qualified cases follows from successful resumption.

## Final readback to run after verified download

Use the original standard-library checker:

`python3 collagen-3d-bovine-calibration/campaign1-audit/check_resume_preservation.py collagen-3d-bovine-calibration/remote-final`

It checks every original final/commission file against literal resume ZIP bytes, compares returned mathematical functions against the preserved prior source, parses the new final files and reports total/new/status counts. It fails on any missing or changed prior bytes, prior-local mismatch or mathematical function change. The parent must separately verify the new downloaded archive's receipt SHA and safely extract paths before this checker is run. Full 160-case numerical qualification remains the existing analysis pipeline's job; bit preservation does not imply equilibrium, stability, energy, resolution or physical validation.

No cancellation-worthy static bug was found in the inspected resume plan.
