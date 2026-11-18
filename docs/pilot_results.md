# Pilot results (preliminary, local SWE-bench 4.1.0 scoring)

| Task | Qwen | Gemma | Qwen tokens | Gemma tokens | Qwen s | Gemma s |
|---|---|---|---|---|---|---|
| django__django-11532 | pass | pass | 722,861 | 90,093 | 481 | 41 |
| django__django-11790 | pass | pass | 912,711 | 155,878 | 367 | 53 |
| django__django-13417 | pass | fail | 880,704 | 244,514 | 339 | 106 |
| django__django-14631 | pass | fail | 1,166,960 | 702,217 | 477 | 441 |
| django__django-16082 | pass | pass | 1,263,307 | 465,147 | 217 | 91 |
| matplotlib__matplotlib-20826 | timeout | fail | 7,230,440 | 368,286 | 1869 | 87 |
| matplotlib__matplotlib-22871 | pass | fail | 1,223,432 | 268,452 | 708 | 82 |
| matplotlib__matplotlib-25775 | pass | fail | 6,169,113 | 587,532 | 785 | 118 |
| matplotlib__matplotlib-26291 | pass | fail | 673,096 | 58,076 | 287 | 36 |
| psf__requests-1921 | fail | fail | 587,385 | 119,316 | 342 | 42 |
| pydata__xarray-4629 | pass | pass | 328,558 | 30,074 | 101 | 16 |
| pydata__xarray-7233 | pass | pass | 747,474 | 102,235 | 249 | 349 |
| pytest-dev__pytest-10081 | pass | fail | 866,344 | 146,312 | 455 | 147 |
| scikit-learn__scikit-learn-25232 | pass | fail | 2,486,529 | 157,173 | 1530 | 137 |
| sphinx-doc__sphinx-8265 | timeout | fail | 5,648,451 | 726,311 | 1802 | 482 |
| sympy__sympy-13091 | pass | fail | 1,724,329 | 108,121 | 466 | 26 |
| sympy__sympy-13877 | pass | pass | 1,653,668 | 152,668 | 534 | 81 |
| sympy__sympy-15875 | fail | fail | 848,649 | 1,355,317 | 916 | 1177 |
| sympy__sympy-16886 | pass | pass | 78,455 | 7,266 | 91 | 12 |
| sympy__sympy-22714 | pass | pass | 1,116,832 | 467,800 | 284 | 179 |

| Outcome | Tasks |
|---|---|
| Both solved | 8 |
| Only Qwen | 8 |
| Only Gemma | 0 |
| Neither | 4 |

| Policy | Resolved (of 20) | Run time (h) | Tokens (M) |
|---|---|---|---|
| Always Qwen | 16 | 3.42 | 36.3 |
| Always Gemma | 8 | 1.03 | 6.3 |
| Token-oracle (fewest tokens among models that solve) | 16 | 2.05 | 18.7 |
| Time-oracle (shortest time among models that solve) | 16 | 2.03 | 19.4 |

Success oracle (solved by at least one model): 16/20.
Notes: one run per model. Timeouts count as unresolved. Tokens are input plus output,
not money. Oracles use known outcomes and exclude routing overhead.
