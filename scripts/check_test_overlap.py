"""Compare agent patches with the official test patches (read-only).

RESET: agent changed a file the test patch also changes. The harness restores it.
COLLISION: agent added a file the test patch also adds. Scoring may break.
"""
import json
import sys

from datasets import load_dataset


def parse(diff):
    files = {}
    current = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current = line.split(" b/", 1)[-1]
            files[current] = "MOD"
        elif current and line.startswith("new file mode"):
            files[current] = "NEW"
        elif current and line.startswith("deleted file mode"):
            files[current] = "DEL"
    return files


pilot = json.load(open("docs/pilot_tasks.json"))
ds = load_dataset(pilot["dataset"], split=pilot["split"], revision=pilot["revision"])
test_patch = {ds[t["index"]]["instance_id"]: ds[t["index"]]["test_patch"] for t in pilot["tasks"]}

for run in sys.argv[1:]:
    rows = [json.loads(line) for line in open(run) if line.strip()]
    resets, collisions = 0, []
    for r in rows:
        agent = parse(r.get("predicted_diff") or "")
        official = parse(test_patch[r["instance_id"]])
        for path, kind in official.items():
            if path not in agent:
                continue
            if kind == "NEW" and agent[path] == "NEW":
                collisions.append(f"{r['instance_id']}: {path}")
            else:
                resets += 1
    print(f"\n{run}")
    print(f"   RESET overlaps (harmless): {resets}")
    print(f"   COLLISIONS: {len(collisions)}")
    for c in collisions:
        print(f"      {c}")
