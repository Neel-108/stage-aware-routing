"""Pick pilot tasks from SWE-bench Verified with a fixed seed.

Same seed, n and revision give the same tasks. Indices follow the order
used by `loc2repair export-verified --start-index`.
"""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset
from huggingface_hub import HfApi

DATASET = "SWE-bench/SWE-bench_Verified"
SPLIT = "test"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--revision", default=None, help="Dataset commit to use. Latest if not set.")
    parser.add_argument("--out", default=None, help="Output file. Default docs/pilot_tasks.json, required with --exclude.")
    parser.add_argument("--exclude", default=None, help="Task JSON whose instance IDs are left out of the pool.")
    args = parser.parse_args()
    out = args.out or "docs/pilot_tasks.json"
    if args.exclude:
        if args.out is None:
            raise SystemExit("STOP: --out is required with --exclude")
        protected = {Path("docs/pilot_tasks.json").resolve(), Path(args.exclude).resolve()}
        if Path(args.out).resolve() in protected:
            raise SystemExit("STOP: --out would overwrite the pilot or exclusion file")

    revision = args.revision or HfApi().dataset_info(DATASET).sha
    ds = load_dataset(DATASET, split=SPLIT, revision=revision)
    pool = range(len(ds))
    excluded = []
    if args.exclude:
        with open(args.exclude, encoding="utf-8") as f:
            excluded = [t["instance_id"] for t in json.load(f)["tasks"]]
        if not excluded:
            raise SystemExit("STOP: exclusion list is empty")
        if len(set(excluded)) != len(excluded):
            raise SystemExit("STOP: exclusion list has duplicate IDs")
        excluded = sorted(excluded)
        ids = set(ds["instance_id"])
        missing = [e for e in excluded if e not in ids]
        if missing:
            raise SystemExit(f"STOP: excluded IDs not in dataset: {missing}")
        skip = set(excluded)
        pool = [i for i in range(len(ds)) if ds[i]["instance_id"] not in skip]
    indices = sorted(random.Random(args.seed).sample(pool, args.n))
    if excluded and any(ds[i]["instance_id"] in skip for i in indices):
        raise SystemExit("STOP: selection overlaps the exclusion list")

    tasks = [
        {
            "index": i,
            "instance_id": ds[i]["instance_id"],
            "repo": ds[i]["repo"],
            "difficulty": ds[i].get("difficulty"),
        }
        for i in indices
    ]
    record = {
        "dataset": DATASET,
        "revision": revision,
        "split": SPLIT,
        "dataset_size": len(ds),
        "seed": args.seed,
        "n": args.n,
        "method": "random.Random(seed).sample(range(dataset_size), n), sorted by index",
        "tasks": tasks,
    }
    if excluded:
        record["method"] = "random.Random(seed).sample(pool, n), pool = all indices minus excluded IDs, sorted by index"
        record["excluded_from"] = args.exclude
        record["excluded_ids"] = excluded
    with open(out, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
        f.write("\n")

    print("revision:", revision)
    for t in tasks:
        print(t["index"], t["instance_id"], t["difficulty"])
    print("tasks:", len(tasks), "unique:", len({t["instance_id"] for t in tasks}), "excluded:", len(excluded))
    print("repos:", Counter(t["repo"] for t in tasks).most_common())


if __name__ == "__main__":
    main()
