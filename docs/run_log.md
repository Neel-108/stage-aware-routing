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
