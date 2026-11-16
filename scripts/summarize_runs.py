"""Summarize a baseline run: status, time, steps, tokens and patch files per task."""
import json
import sys

SOURCE_EXCLUDE = ("mamba_root/", ".sandbox_home/", "reproduce", "mock_")

path = sys.argv[1]
rows = [json.loads(line) for line in open(path) if line.strip()]

print(f"{'instance_id':40} {'status':8} {'sec':>6} {'steps':>5} {'in_tok':>9} {'out_tok':>7} {'files':>5}  flags")
for r in sorted(rows, key=lambda x: x["instance_id"]):
    u = r.get("repair_usage") or {}
    diff = r.get("predicted_diff") or ""
    files = [l[6:] for l in diff.splitlines() if l.startswith("+++ ")]
    flags = sorted({p for f in files for p in SOURCE_EXCLUDE if p in f})
    print(
        f"{r['instance_id']:40} {r.get('status',''):8} {r.get('elapsed_sec') or 0:6.0f} "
        f"{u.get('agent_steps') or 0:5.0f} {u.get('input_tokens') or 0:9.0f} "
        f"{u.get('output_tokens') or 0:7.0f} {len(files):5}  {','.join(flags)}"
    )
print("tasks:", len(rows))
