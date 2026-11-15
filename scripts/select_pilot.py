"""Pick pilot tasks from SWE-bench Verified with a fixed seed.

Same seed, n and revision give the same tasks. Indices follow the order
used by `loc2repair export-verified --start-index`.
"""
import argparse
import json
import random

from datasets import load_dataset
from huggingface_hub import HfApi

DATASET = "SWE-bench/SWE-bench_Verified"
SPLIT = "test"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--revision", default=None, help="Dataset commit to use. Latest if not set.")
    parser.add_argument("--out", default="docs/pilot_tasks.json")
    args = parser.parse_args()

    revision = args.revision or HfApi().dataset_info(DATASET).sha
    ds = load_dataset(DATASET, split=SPLIT, revision=revision)
    indices = sorted(random.Random(args.seed).sample(range(len(ds)), args.n))

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
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
        f.write("\n")

    print("revision:", revision)
    for t in tasks:
        print(t["index"], t["instance_id"], t["difficulty"])


if __name__ == "__main__":
    main()
