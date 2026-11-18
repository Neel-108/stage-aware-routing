# Run log

## 2026-11-15: pipeline check, task astropy__astropy-12907 (baseline arm, 1 task)

| | Qwen3.8 | Gemma-4-26B-A4B-it |
|---|---|---|
| Status | ok | ok |
| Elapsed (s) | 350 | 262 |
| Agent steps | 56 | 30 |
| Input / output tokens (summed over all model calls) | 934,140 / 43,262 | 497,759 / 27,906 |
| Files changed | astropy/modeling/separable.py, test file, changelog | mock_erfa.py, reproduce_issue.py (no source file changed) |

Notes:
- Purpose: Confirm the pipeline runs end to end with both models. 
- Repair success is unknown until the SWE-bench harness scores the patches.
- The repair sandbox has no project dependencies installed. Gemma created a mock of erfa, which suggests missing dependencies affected its attempt and it is not proven.
- Both models ran in the same sandbox image, so conditions are consistent. Missing dependencies may still affect models differently.
- Live container check during the Gemma run: user 1000:1000, bridge network, read-only root, all capabilities dropped, 4 GB memory, 2 CPUs, 512 process limit.

## 2026-11-16: pilot, 20 tasks (baseline arm)

Task list: docs/pilot_tasks.json. Same tasks, sandbox, timeout (1800 s) and worker count for both models.

| | Qwen3.8 | Gemma-4-26B-A4B-it |
|---|---|---|
| Finished (ok) | 18 | 20 |
| Timeout | 2 (matplotlib-20826, sphinx-8265) | 0 |
| Total run time | about 3.4 h | about 1 h |
| Typical agent steps | 50 to 80 | 10 to 35 |
| Tasks with a change to an existing file | 20 | 18 |
| Tasks with helper files added (reproduce, patch scripts) | 1 (changelog file only) | 19 |
| Tasks with environment files in the patch | 1 (matplotlib-20826) | 0 |

Notes:
- Repair success is not known yet. Patches still need scoring with the SWE-bench harness.
- Qwen matplotlib-20826: the patch has 2 source changes and 9,327 new environment files (mamba_root, toolchain, micromamba, build logs). The agent tried to build the project inside the sandbox.
- Gemma matplotlib-26291 and pytest-10081: no existing file changed, only helper scripts. These cannot fix the issue.
- Qwen sympy-13091 changes 23 files. This matches the scope of the issue (comparison methods in many classes).
- The sandbox has no project dependencies. Both models spent effort working around this.
- Live container check during both runs: user 1000:1000, bridge network, read-only root, all capabilities dropped, 4 GB memory, 2 CPUs, 512 processes.

## 2026-11-18: pilot scoring (local SWE-bench 4.1.0, preliminary)

Results and oracle bounds: docs/pilot_results.md (made by scripts/pilot_results.py).
- Qwen3.8 resolved 16/20, Gemma-4 resolved 8/20. No scoring errors.
- All 8 Gemma successes were also solved by Qwen in these runs.
- Success oracle: 16/20. Token-oracle: 16/20 with 18.7M tokens (Qwen alone: 36.3M).
- The harness image pull failed silently. Images were pulled by hand with VPN off, then scored with --clean false.
- Dataset revision at scoring time matched the pinned revision 78f471bf.
