"""Make a sanitized copy of a prepared task file for the exploration step (D13).

Test names (fail_to_pass, pass_to_pass) and dataset hints (hints_text) are emptied,
so the exploration prompt is the issue text only. The input file is never changed.
"""
import argparse
import json
import os
import sys

EMPTIED = {"fail_to_pass": [], "pass_to_pass": [], "hints_text": ""}
FORBIDDEN_KEYS = ("patch", "test_patch", "gold_files", "gold_patch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-in", required=True)
    parser.add_argument("--tasks-out", required=True)
    args = parser.parse_args()

    if os.path.abspath(args.tasks_in) == os.path.abspath(args.tasks_out):
        sys.exit("STOP: output would overwrite the input")
    if os.path.exists(args.tasks_out):
        sys.exit("STOP: output file already exists")

    rows = [json.loads(line) for line in open(args.tasks_in, encoding="utf-8") if line.strip()]
    if not rows:
        sys.exit("STOP: input has no tasks")
    for r in rows:
        bad = [k for k in r if k in FORBIDDEN_KEYS]
        if bad:
            sys.exit(f"STOP: {r.get('instance_id')} has reference fields {bad}")

    clean, mentions = [], 0
    for r in rows:
        hidden = [str(t) for t in (r.get("fail_to_pass") or []) + (r.get("pass_to_pass") or [])]
        hints = (r.get("hints_text") or "").strip()
        c = dict(r)
        c.update(EMPTIED)
        others = json.dumps({k: v for k, v in c.items() if not k.startswith("issue_")})
        leaked = [t for t in hidden if t and t in others] + ([hints[:40]] if hints and hints in others else [])
        if leaked:
            sys.exit(f"STOP: {r.get('instance_id')} still contains removed text in other fields")
        issue = " ".join(str(c.get(k) or "") for k in ("issue_text", "issue_title", "issue_body", "issue_comments"))
        if any(t and t in issue for t in hidden):
            mentions += 1
        clean.append(c)

    os.makedirs(os.path.dirname(os.path.abspath(args.tasks_out)), exist_ok=True)
    with open(args.tasks_out, "w", encoding="utf-8") as f:
        for c in clean:
            f.write(json.dumps(c) + "\n")

    check = [json.loads(line) for line in open(args.tasks_out, encoding="utf-8") if line.strip()]
    assert [r["instance_id"] for r in check] == [r["instance_id"] for r in rows]
    assert all(r[k] == v for r in check for k, v in EMPTIED.items())
    print(f"tasks: {len(check)} | test names and hints emptied in all | "
          f"issue text itself names a hidden test in {mentions} task(s) (kept, part of the issue)")


if __name__ == "__main__":
    main()
