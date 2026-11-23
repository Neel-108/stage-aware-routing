"""Pilot results: per-task outcome and oracle bounds.

Inputs: run records (baseline.jsonl) and local harness reports.
Timeouts count as unresolved (D8). Oracles use known outcomes and
exclude routing overhead, so they are bounds, not methods.
"""
import argparse
import json
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--qwen-run", default="runs/pilot/qwen38/baseline/baseline.jsonl")
parser.add_argument("--qwen-report", default="runs/pilot/harness/qwen3.8.pilot-qwen38.json")
parser.add_argument("--gemma-run", default="runs/pilot/gemma4/baseline/baseline.jsonl")
parser.add_argument("--gemma-report", default="runs/pilot/harness/gemma-4-26B-A4B-it.pilot-gemma4.json")
parser.add_argument("--expected-tasks", type=int, default=20)
parser.add_argument("--out", default="docs/pilot_results.md")
args = parser.parse_args()

EXPECTED_TASKS = args.expected_tasks
RUNS = {
    "qwen": (args.qwen_run, args.qwen_report),
    "gemma": (args.gemma_run, args.gemma_report),
}


def need(value, what):
    if value is None:
        sys.exit(f"Missing data: {what}")
    return value


data = {}
task_sets = {}
for model, (run_path, report_path) in RUNS.items():
    report = json.load(open(report_path))
    resolved = set(report["resolved_ids"])
    scored = resolved | set(report["unresolved_ids"])
    if report["error_ids"]:
        sys.exit(f"{model}: harness errors {report['error_ids']}")
    rows = [json.loads(line) for line in open(run_path) if line.strip()]
    ids = [r["instance_id"] for r in rows]
    if len(ids) != EXPECTED_TASKS or len(set(ids)) != EXPECTED_TASKS:
        sys.exit(f"{model}: expected {EXPECTED_TASKS} unique tasks, found {len(set(ids))} unique in {len(ids)} rows")
    task_sets[model] = set(ids)
    for r in rows:
        iid = r["instance_id"]
        if r.get("status") == "ok" and iid not in scored:
            sys.exit(f"{model} {iid}: ok run was not scored by the harness")
        u = need(r.get("repair_usage"), f"{model} {iid} repair_usage")
        data.setdefault(iid, {})[model] = {
            "ok": iid in resolved,
            "status": r.get("status"),
            "sec": need(r.get("elapsed_sec"), f"{model} {iid} elapsed_sec"),
            "tok": need(u.get("input_tokens"), f"{model} {iid} input_tokens")
                   + need(u.get("output_tokens"), f"{model} {iid} output_tokens"),
        }

if task_sets["qwen"] != task_sets["gemma"]:
    sys.exit("Qwen and Gemma task sets differ")


def best(d, key):
    winners = [m for m in d if d[m]["ok"]] or list(d)
    return min(winners, key=lambda m: d[m][key])


def totals(choice):
    ok = sum(data[i][choice(i)]["ok"] for i in data)
    sec = sum(data[i][choice(i)]["sec"] for i in data)
    tok = sum(data[i][choice(i)]["tok"] for i in data)
    return ok, sec, tok


def label(x):
    return "pass" if x["ok"] else ("timeout" if x["status"] == "timeout" else "fail")


n = len(data)
lines = ["# Pilot results (preliminary, local SWE-bench 4.1.0 scoring)", "",
         "| Task | Qwen | Gemma | Qwen tokens | Gemma tokens | Qwen s | Gemma s |",
         "|---|---|---|---|---|---|---|"]
for i in sorted(data):
    q, g = data[i]["qwen"], data[i]["gemma"]
    lines.append(f"| {i} | {label(q)} | {label(g)} | {q['tok']:,.0f} | {g['tok']:,.0f} | {q['sec']:.0f} | {g['sec']:.0f} |")

both = sum(d["qwen"]["ok"] and d["gemma"]["ok"] for d in data.values())
only_q = sum(d["qwen"]["ok"] and not d["gemma"]["ok"] for d in data.values())
only_g = sum(d["gemma"]["ok"] and not d["qwen"]["ok"] for d in data.values())
neither = n - both - only_q - only_g

lines += ["", "| Outcome | Tasks |", "|---|---|",
          f"| Both solved | {both} |", f"| Only Qwen | {only_q} |",
          f"| Only Gemma | {only_g} |", f"| Neither | {neither} |", "",
          f"| Policy | Resolved (of {n}) | Run time (h) | Tokens (M) |", "|---|---|---|---|"]
policies = [
    ("Always Qwen", lambda i: "qwen"),
    ("Always Gemma", lambda i: "gemma"),
    ("Token-oracle (fewest tokens among models that solve)", lambda i: best(data[i], "tok")),
    ("Time-oracle (shortest time among models that solve)", lambda i: best(data[i], "sec")),
]
for name, fn in policies:
    ok, sec, tok = totals(fn)
    lines.append(f"| {name} | {ok} | {sec / 3600:.2f} | {tok / 1e6:.1f} |")

lines += ["", f"Success oracle (solved by at least one model): {both + only_q + only_g}/{n}.",
          "Notes: one run per model. Timeouts count as unresolved. Tokens are input plus output,",
          "not money. Oracles use known outcomes and exclude routing overhead.",
          "For tasks neither model solved, the oracle counts the cheaper of the two runs."]

open(args.out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
