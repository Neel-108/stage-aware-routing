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

D13 (2026-11-26, DRAFT, waiting for the scientific advisor's feedback): Laya routing design, fixed before any main result is inspected.

1. Exploration (Gemma-4)
- Each of the 50 main tasks explored once with Gemma, in the same sandbox image, under the watchdog (D12). One attempt, no retries, 600 s per task.
- Implementation: Loc2Repair run-baseline with its existing --repair-cmd-template option and our own config (configs/explore.yaml). Loc2Repair itself is unchanged. The task file is sanitized (scripts/make_explore_tasks.py): test names and dataset hints are removed, so the prompt is the issue text only.
- Read-only: instructed by the prompt, as in Loc2Repair's localization stage. The agent works on a throwaway copy of the snapshot with a read-only root filesystem. The dataset folder, gold patches, test patches and repair results are not mounted. Any change in the workspace diff after the run makes the exploration a failure. An empty diff shows no remaining changes, not strictly read-only execution. A read-only mount would need a change to Loc2Repair (D2).
- Output: a report with fixed headings: Bug / Relevant files / Possible cause / Estimated difficulty (easy, medium or hard) / Uncertainties. Target length 150 to 250 words.
- Valid report (scripts/extract_reports.py): run status ok, workspace unchanged, report submitted, all five sections present in order and non-empty, at most 250 words, difficulty easy, medium or hard, and at least one listed file exists in the snapshot (relative paths only, no '..', no symlinks outside). No minimum length: in the smoke test (pilot task django__django-11532, 28 Nov) a complete and specific report had 118 words, and a minimum would push such reports into the Qwen fallback.
- Failure (no valid report within 600 s): recorded with its reason, tokens and time. Laya and the rule fall back to Qwen for that task.

2. Laya decision
- Request: state.request = the report text.
- Question: type "choice", instructions "Which model should repair this bug?"
  Criteria: "gemma-4" = "The bug is localized to one or two files, the cause is clear, estimated difficulty is easy and few uncertainties remain."
  "qwen3.8" = "The bug spans several files or components and the cause is unclear, the estimated difficulty is medium or hard, or important uncertainties remain."
- Decision: the returned choice. Probabilities logged and never used for tuning.
- Truncation (512-token limit): if truncated or state_tokens_dropped > 0, each section is shortened from the end while all headings are kept and the call is repeated once. Still truncated, or a call error after 3 tries: fall back to Qwen, counted as a Laya failure.

3. Policies (same 50 tasks, same order as docs/main_tasks.json; outcomes looked up from the r2 repair runs)
- Always-Qwen, Always-Gemma.
- Random: each task to Gemma with p = 0.5, random.Random(2028), in task-list order.
- Matched random: random.Random(2028) picks exactly as many tasks for Gemma as Laya does.
- Simple rule: Gemma if the report names exactly one distinct relevant file that exists in the task's repository snapshot, otherwise Qwen.
- Laya with report.
- Success, token and time oracles: bounds only.

4. Ablation
- Laya without exploration: state.request = the issue text, cut from the end to fit under the input limit. Same question and criteria.

5. Overhead (policy-specific, failed attempts and retries included)
- Always-Qwen, Always-Gemma, Random, Matched random: no overhead.
- Simple rule: exploration overhead only.
- Laya with report: exploration + Laya calls.
- Laya without exploration: Laya calls only.
- Recorded per task: exploration input and output tokens, time, failures; per Laya call: input_tokens, state_tokens, state_tokens_dropped, truncated, latency, retries, failures.
- Missing usage is recorded as missing, never as 0. Repair and overhead are reported separately and as totals.

6. Scoring and statistics
- SWE-bench 4.1.0 harness as in the pilot or lab scoring if available. Timeouts are unresolved (D8).
- Confirmed infrastructure failures (D12) excluded from paired comparisons. Coverage over all 50 tasks is reported and every comparison uses the common evaluable task set.
- Resolved: paired exact McNemar vs always-Qwen and vs always-Gemma.
- Tokens and time: paired bootstrap, 10,000 resamples, seed 2029, 95% confidence intervals for differences.
- All results reported, including where Laya loses. With 50 tasks and one run per model a non-significant difference is not evidence of equivalence.

7. Repair runs are not changed. The report is used only for the routing decision.

8. End-to-end demonstration: The full pipeline (explore, decide, run the chosen repair model) runs live on 1 to 2 tasks, to show the working system. These runs are separate from the 50-task evaluation.

9. Limitation of the completed repair runs: the repair prompt included the dataset hints text when present (Loc2Repair default, runtime/runner/stages.py). The same for both models and the pilot. No rerun.
