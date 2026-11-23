# Decisions

D1 (2026-11-13): I reuse the Loc2Repair baseline unchanged, pinned at commit 399b4dca53e6dc3e06c4531be3222dc7ec4d4d3f.

D2 (2026-11-13): The Loc2Repair code stays in its own folder (~/nir/loc2repair) and is never edited. All my work lives in this repository.

D3 (2026-11-14): The .env file lives in this repository and is ignored by Git. Each step loads only the secrets it needs.

D4 (2026-11-14): The sandbox uses Docker's bridge network. A test container reached the model endpoint without host networking.

D5 (2026-11-14): Loc2Repair runs its commands from its own folder, so every path I pass to it is absolute and points into this repository.

D6 (2026-11-15): Pilot uses 20 tasks from SWE-bench Verified, chosen with seed 2026 at dataset revision 78f471bf655a3137b2e8a75af1501690ec009ec3 (docs/pilot_tasks.json). The exporter loads the latest revision, so task IDs are checked after export (scripts/check_pilot_export.py). Task contents are not checked.

D7 (2026-11-16): Before scoring, new files created by the agent for its environment are removed from patches. Confirmed so far: mamba_root/, toolchain/, micromamba, build.log, build2.log. Helper scripts (reproduce, patch scripts) stay in. Original patches are kept unchanged, cleaned copies are stored separately with a list of every removed path, and raw and cleaned scores are kept apart. The same rule applies to every model and condition. Timeouts stay timeouts.

D8 (2026-11-18): Scoring follows the Loc2Repair default. Runs that did not finish (timeouts) are not scored and count as unresolved. Success rates use all 20 tasks as the denominator.

D9 (2026-11-23): Unit tests for the analysis scripts run locally with pytest (tests/, pytest.ini). pytest only searches tests/, because data/ and runs/ hold task repositories with their own tests. 