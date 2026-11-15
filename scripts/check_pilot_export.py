"""Check that exported pilot tasks match docs/pilot_tasks.json exactly."""
import json
import sys

selected = [t["instance_id"] for t in json.load(open("docs/pilot_tasks.json"))["tasks"]]
manifest = "data/pilot/exported_swebench_verified/manifest.jsonl"
exported = [json.loads(line)["instance_id"] for line in open(manifest) if line.strip()]

missing = sorted(set(selected) - set(exported))
extra = sorted(set(exported) - set(selected))
duplicates = sorted({i for i in exported if exported.count(i) > 1})

print("selected:", len(selected), "| exported:", len(exported))
print("missing:", missing)
print("extra:", extra)
print("duplicates:", duplicates)

if missing or extra or duplicates:
    print("RESULT: MISMATCH, stop here")
    sys.exit(1)
print("RESULT: OK, all 20 IDs match")
