"""Check that exported tasks match a selected task list exactly (default: the pilot)."""
import argparse
import json
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--tasks", default="docs/pilot_tasks.json")
parser.add_argument("--manifest", default="data/pilot/exported_swebench_verified/manifest.jsonl")
args = parser.parse_args()

selected = [t["instance_id"] for t in json.load(open(args.tasks))["tasks"]]
manifest = args.manifest
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
print(f"RESULT: OK, all {len(selected)} IDs match")
