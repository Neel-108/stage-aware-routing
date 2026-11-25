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

D10 (2026-11-24): The main experiment uses 50 SWE-bench Verified tasks chosen with seed 2027 at dataset revision 78f471bf655a3137b2e8a75af1501690ec009ec3, from the 480 tasks left after removing the 20 pilot tasks (docs/main_tasks.json, scripts/select_pilot.py --exclude docs/pilot_tasks.json). Plain random sampling with no hand-picking. The list is committed before any run and is not changed after seeing results. Repo mix: django 28, sympy 9, pytest 4, sphinx 3, scikit-learn 2, astropy, matplotlib, xarray and pylint 1 each. With seed 2026 and no exclusion, the script still gives the same 20 pilot tasks (checked byte for byte).

D11 (2026-11-25): Before each main repair run, a gate sends 3 unique short prompts to the repair model (max_tokens 1024). Each reply must arrive within 10 s and be valid (it repeats a random code and gives the right answer), or the run does not start. The same gate applies to every model. Results are appended to pregate.txt next to the run folder. A fast gate does not guarantee a fast run. Thresholds set from probes on 25 Nov (Gemma 0.1 to 0.2 s, Qwen 1.6 to 2.3 s).

D12 (2026-11-25): A row with zero or missing agent steps is flagged as a suspected infrastructure failure and investigated before scoring. Confirmed infrastructure failures are excluded from model-performance calculations and reported separately. The same rule applies to every model. Runs are supervised (scripts/supervise_run.py): the run stops when the model server is unreachable for 3 checks in a row (one model-list request every 60 s), when a row with 0 steps appears, or on Ctrl+C. At the end, all rows must be complete, match the task list exactly and have agent steps. Limits: a model-list check proves the API is reachable, not that inference works; a row written within the detection delay may still be invalid; automatic container cleanup works only if the container's mount matches the run folder. Normal timeouts with real agent steps stay valid results. Aborted runs are kept and logged.
