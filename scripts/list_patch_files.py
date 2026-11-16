"""Summarize the files each saved patch touches (read-only).

MOD = existing file changed, NEW = file added, DEL = file deleted.
New files are grouped by top folder.
"""
import json
import sys
from collections import Counter


def parse(diff):
    files = []
    current = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current = {"path": line.split(" b/", 1)[-1], "kind": "MOD"}
            files.append(current)
        elif current and line.startswith("new file mode"):
            current["kind"] = "NEW"
        elif current and line.startswith("deleted file mode"):
            current["kind"] = "DEL"
    return files


rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
changed_existing = 0

for r in sorted(rows, key=lambda x: x["instance_id"]):
    files = parse(r.get("predicted_diff") or "")
    kinds = Counter(f["kind"] for f in files)
    existing = [f for f in files if f["kind"] in ("MOD", "DEL")]
    if existing:
        changed_existing += 1
    new_tops = Counter(f["path"].split("/")[0] for f in files if f["kind"] == "NEW")
    print(f"{r['instance_id']}  {r.get('status')}  MOD={kinds['MOD']} NEW={kinds['NEW']} DEL={kinds['DEL']}")
    for f in existing[:10]:
        print(f"   {f['kind']} {f['path']}")
    if len(existing) > 10:
        print(f"   ... {len(existing) - 10} more existing files")
    if new_tops:
        print("   NEW by folder: " + ", ".join(f"{k} ({v})" for k, v in new_tops.most_common(5)))

print(f"\nTasks that change at least one existing file: {changed_existing}/{len(rows)}")
