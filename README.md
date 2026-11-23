# Stage-Aware Model Routing for Coding Agents

ITMO University, Master's research project (NIR), semester 1, 2026/27.
Author: Swapnil Panchal. Supervisor: Prof. Sergey Ivanov. Scientific advisor: Mohammad Nour Al Awad.

## Research question
A coding-agent workflow has several stages such as repository exploration, implementation, debugging and verification etc. This research project studies whether these stages should use different LLMs depending on the capability each stage needs.

## First step in this semester
The first experiments focus on two stages: exploration and repair. An exploration step writes a short report about the task. Laya, a decision model, reads the report and selects the repair model (Qwen or Gemma). This selection is compared with always-Qwen, always-Gemma, random and a simple rule on the same tasks, using resolved rate, tokens and run time.

## Related work
- Loc2Repair: localization followed by repair on SWE-bench Verified, with a fixed repair model.
- Scrouting: a small model explores the repository, then a learned router picks the repair model.
- General LLM routing methods choose a model per request, mostly outside coding agents.

## Status
| Part | Status |
|---|---|
| Baseline pilot (20 tasks, Qwen and Gemma) | Done, scored locally |
| Exploration step and Laya selection | Planned |
| Comparison with baselines | Planned |
| Ablation: Laya with and without the report | Planned |

## Hypothesis and constraints
Hypothesis: Laya keeps a resolved rate close to always-Qwen while using fewer tokens and less time, with exploration and Laya costs included. A negative result is a valid outcome.
- Models: Qwen3.8 and Gemma-4-26B-A4B-it on the ITMO server. Laya as the decision model.
- Benchmark: SWE-bench Verified, random samples with a fixed seed.
- Same sandbox, timeout (1800 s) and scoring for every policy. One run per configuration.
- Metrics: resolved rate, input and output tokens, run time.

## Quickstart
Setup used for all runs: Windows 11, WSL2 (Ubuntu 26.04), Docker Desktop with WSL integration, Python 3.11.18 (uv).
Full steps, including dependency checks and sandbox safety checks: docs/reproduce.md.

## Pilot results (20 tasks, preliminary local scoring)
| | Qwen3.8 | Gemma-4 |
|---|---|---|
| Resolved | 16/20 | 8/20 |
| Timeouts | 2 | 0 |
| Run time | 3.4 h | 1.0 h |
| Tokens (input + output) | 36.3M | 6.3M |

All 8 Gemma successes were also solved by Qwen in this pilot. A token-oracle keeps 16/20 with 18.7M tokens. This is an idealized lower bound on token use, based on known outcomes and excluding exploration and routing overhead. Details: docs/pilot_results.md.

## Limitations
- Small samples and one run per configuration.
- The repair sandbox lacks some project dependencies, so agents cannot always run project code.
- Scores so far come from a local SWE-bench 4.1.0 run. Final scores will come from the lab environment.
- The exporter and the harness load the latest dataset revision. At scoring time it matched the pinned revision 78f471bf. At export time only task IDs were checked, not task contents.

## Repository layout
    docs/        decisions, run log, reproduce guide, pilot task list and results, literature review
    scripts/     task selection, export checks, patch inspection, result tables, Laya test
    tests/       unit tests for the analysis scripts (synthetic data)
    requirements.txt, requirements-lock.txt, .env.example, pytest.ini
