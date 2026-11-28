"""Build reports.jsonl from an exploration run (D13).

One line per task: the report text, its parts, checks, tokens and time.
A report is valid only if the run finished, nothing in the repository changed,
all five headings are present in order and none is empty, it has at most 250 words, the difficulty
is easy, medium or hard, and at least one listed file exists in the snapshot.
Invalid reports are kept with their reason and their tokens and time.
Missing usage stays None, never 0.
"""
import argparse
import json
import os
import re
import sys

HEADINGS = ["Bug", "Relevant files", "Possible cause", "Estimated difficulty", "Uncertainties"]
DIFFICULTY = {"easy", "medium", "hard"}


def parse(text):
    """Split the report into its five parts. Returns (parts, problem)."""
    pattern = re.compile(r"^\s*(" + "|".join(re.escape(h) for h in HEADINGS) + r")\s*:", re.MULTILINE)
    found = [(m.group(1), m.start(), m.end()) for m in pattern.finditer(text)]
    names = [f[0] for f in found]
    if names != HEADINGS:
        return None, f"headings found {names}"
    parts = {}
    for i, (name, _, end) in enumerate(found):
        stop = found[i + 1][1] if i + 1 < len(found) else len(text)
        parts[name] = text[end:stop].strip()
    return parts, None


def clean_path(p):
    p = p.strip().strip("`'\"").strip()
    return p[2:] if p.startswith("./") else p


def in_snapshot(p, snap):
    """True only for a relative path, without '..', that resolves to a file inside the snapshot."""
    if not p or os.path.isabs(p) or ".." in p.replace("\\", "/").split("/"):
        return False
    real, root = os.path.realpath(os.path.join(snap, p)), os.path.realpath(snap)
    return os.path.commonpath([real, root]) == root and os.path.isfile(real)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--tasks", required=True, help="sanitized task file used for the run")
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if os.path.exists(args.out):
        sys.exit("STOP: output file already exists")

    tasks = [json.loads(l) for l in open(args.tasks, encoding="utf-8") if l.strip()]
    task_ids = [t["instance_id"] for t in tasks]
    if len(set(task_ids)) != len(task_ids):
        sys.exit("STOP: duplicate task IDs in the task file")
    rows = {}
    for l in open(os.path.join(args.run_dir, "baseline.jsonl"), encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            iid = r.get("instance_id")
            if iid in rows:
                sys.exit(f"STOP: duplicate run row for {iid}")
            if iid not in task_ids:
                sys.exit(f"STOP: run row for unexpected task {iid}")
            rows[iid] = r

    out = []
    for t in tasks:
        iid = t["instance_id"]
        r = rows.get(iid)
        rec = {"instance_id": iid, "valid": False, "reason": None, "report": None, "words": None,
               "difficulty": None, "files_listed": [], "files_valid": [], "repo_changed": None,
               "status": None, "elapsed_sec": None, "input_tokens": None, "output_tokens": None,
               "agent_steps": None}
        if r is None:
            rec["reason"] = "no run row"
            out.append(rec)
            continue
        u = r.get("repair_usage") or {}
        rec.update(status=r.get("status"), elapsed_sec=r.get("elapsed_sec"),
                   input_tokens=u.get("input_tokens"), output_tokens=u.get("output_tokens"),
                   agent_steps=u.get("agent_steps"))
        diff_text, changed = r.get("predicted_diff"), r.get("changed_files")
        if isinstance(diff_text, str) and isinstance(changed, list):
            rec["repo_changed"] = bool(diff_text or changed)

        traj_path = os.path.join(args.run_dir, iid, "repair.traj.json")
        info = {}
        if os.path.exists(traj_path):
            info = json.load(open(traj_path, encoding="utf-8")).get("info") or {}
        text = (info.get("submission") or "").strip()
        rec["report"] = text or None

        if r.get("status") != "ok":
            rec["reason"] = f"run status {r.get('status')}"
        elif rec["repo_changed"] is None:
            rec["reason"] = "modification status unknown (diff fields missing)"
        elif rec["repo_changed"]:
            rec["reason"] = "repository changed"
        elif info.get("exit_status") != "Submitted" or not text:
            rec["reason"] = f"no submitted report (exit {info.get('exit_status')})"
        else:
            parts, problem = parse(text)
            words = len(text.split())
            rec["words"] = words
            if problem:
                rec["reason"] = problem
            else:
                diff = parts["Estimated difficulty"].strip().strip(".").lower()
                rec["difficulty"] = diff
                listed = [clean_path(p) for p in parts["Relevant files"].replace("\n", ",").split(",") if clean_path(p)]
                snap = os.path.join(args.dataset_root, t["snapshot_path"])
                valid = sorted({p for p in listed if in_snapshot(p, snap)})
                rec["files_listed"], rec["files_valid"] = listed, valid
                empty = [h for h in HEADINGS if not parts[h]]
                if empty:
                    rec["reason"] = f"empty sections {empty}"
                elif words > 250:
                    rec["reason"] = f"{words} words, above 250"
                elif diff not in DIFFICULTY:
                    rec["reason"] = f"difficulty '{diff}' not easy, medium or hard"
                elif not valid:
                    rec["reason"] = "no listed file exists in the snapshot"
                else:
                    rec["valid"] = True
        out.append(rec)

    with open(args.out, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")
    n_valid = sum(r["valid"] for r in out)
    print(f"tasks: {len(out)} | valid reports: {n_valid} | invalid: {len(out) - n_valid}")
    for r in out:
        if not r["valid"]:
            print(f"  invalid: {r['instance_id']}: {r['reason']}")


if __name__ == "__main__":
    main()
