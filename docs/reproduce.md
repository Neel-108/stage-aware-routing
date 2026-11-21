# Reproducing the pilot

Commands as used for the pilot. Paths assume ~/nir/loc2repair and ~/nir/stage-aware-routing.
Loc2Repair runs its commands from its own folder, so every path passed to it is absolute.
Pinned dataset revision: 78f471bf655a3137b2e8a75af1501690ec009ec3.

Sections 1, 2 and 4 each run in their own bash process. A failed check stops that section and leaves the terminal open.

## 1. Setup

```bash
mkdir -p ~/nir && cd ~/nir
git clone https://github.com/mohammad-nour-alawad/Loc2Repair.git loc2repair
git -C loc2repair checkout 399b4dca53e6dc3e06c4531be3222dc7ec4d4d3f
git clone git@github.com:Neel-108/stage-aware-routing.git stage-aware-routing   # private, access required
cd ~/nir/loc2repair && uv venv --python 3.11 .venv
```

Install, check versions against the recorded environment, then build the sandbox image:

```bash
bash <<'BASH'
set -eo pipefail
cd "$HOME/nir/loc2repair"
source .venv/bin/activate
set -u

uv pip install -e ".[dev]"
uv pip install -r "$HOME/nir/stage-aware-routing/requirements-lock.txt"

if ! uv pip freeze | grep -v '^-e ' | diff -q - "$HOME/nir/stage-aware-routing/requirements-lock.txt"; then
    echo "STOP: Installed dependencies differ from the recorded environment."
    exit 1
fi

echo "Dependencies verified."
bash ./scripts/build_sandbox_image.sh loc2repair-sandbox:latest
BASH
```

Settings:

```bash
cd ~/nir/stage-aware-routing
cp .env.example .env      # fill in keys and endpoints
chmod 600 .env
```

## 2. Dataset check, task selection and export

The export folder must not contain an earlier export, because the manifest is appended. The block stops if it does. Existing data is never deleted.

```bash
bash <<'BASH'
set -eo pipefail
source "$HOME/nir/loc2repair/.venv/bin/activate"
set -u
cd "$HOME/nir/stage-aware-routing"

OUT="$HOME/nir/stage-aware-routing/data/pilot/exported_swebench_verified"
if [ -e "$OUT" ] && [ ! -d "$OUT" ]; then
    echo "STOP: Export path exists but is not a directory."
    exit 1
fi

if [ -d "$OUT" ] && [ -n "$(find "$OUT" -mindepth 1 -print -quit)" ]; then
    echo "STOP: Export folder contains existing data. Use a new folder."
    exit 1
fi

python3 - <<'PY'
from huggingface_hub import HfApi
expected = "78f471bf655a3137b2e8a75af1501690ec009ec3"
actual = HfApi().dataset_info("SWE-bench/SWE-bench_Verified").sha
if actual != expected:
    raise SystemExit(f"STOP: Dataset revision mismatch: {actual}")
print("Dataset revision verified.")
PY

python3 scripts/select_pilot.py --revision 78f471bf655a3137b2e8a75af1501690ec009ec3

indices=$(python3 - <<'PY'
import json
tasks = json.load(open("docs/pilot_tasks.json"))["tasks"]
assert len(tasks) == 20
assert len({t["index"] for t in tasks}) == 20
print(" ".join(str(t["index"]) for t in tasks))
PY
)

github_token=$(grep '^github_token=' .env | cut -d= -f2-)
export github_token
trap 'unset github_token' EXIT

for i in $indices; do
    loc2repair export-verified --split test --start-index "$i" --limit 1 \
      --append-manifest --out-root "$OUT"
done
unset github_token

python3 scripts/check_pilot_export.py

loc2repair prepare --dataset-root "$OUT" \
  --out-root "$HOME/nir/stage-aware-routing/data/pilot/protocol" \
  --split-name verified_test

echo "Dataset preparation completed."
BASH
```

## 3. Repair runs (ITMO VPN on)

Load settings, then remove credentials the repair runs do not need:

```bash
source ~/nir/loc2repair/.venv/bin/activate
cd ~/nir/stage-aware-routing
set -a; source .env; set +a
unset github_token LAYA_URL LAYA_API_KEY
```

The test lines stop the run unless the Docker sandbox and the intended model are set. Without LOC_REPAIR_SANDBOX_MODE=docker, Loc2Repair runs agent commands directly on the host.

### 3a. Qwen3.8

```bash
export REPAIR_MODEL=qwen3.8
test "$LOC_REPAIR_SANDBOX_MODE" = docker && \
test "$LOC_REPAIR_SANDBOX_IMAGE" = loc2repair-sandbox:latest && \
test "$LOC_REPAIR_SANDBOX_NETWORK" = bridge && \
test "$REPAIR_MODEL" = qwen3.8 && \
loc2repair run-baseline \
  --task-file "$HOME/nir/stage-aware-routing/data/pilot/protocol/tasks/verified_test.jsonl" \
  --dataset-root "$HOME/nir/stage-aware-routing/data/pilot/exported_swebench_verified" \
  --runs-dir "$HOME/nir/stage-aware-routing/runs/pilot/qwen38/baseline" \
  --out "$HOME/nir/stage-aware-routing/runs/pilot/qwen38/baseline/baseline.jsonl" \
  --workers 1 --timeout 1800 --resume \
  || { echo "BLOCKED or FAILED"; false; }
```

### 3b. Gemma-4-26B-A4B-it

```bash
export REPAIR_MODEL=gemma-4-26B-A4B-it
test "$LOC_REPAIR_SANDBOX_MODE" = docker && \
test "$LOC_REPAIR_SANDBOX_IMAGE" = loc2repair-sandbox:latest && \
test "$LOC_REPAIR_SANDBOX_NETWORK" = bridge && \
test "$REPAIR_MODEL" = gemma-4-26B-A4B-it && \
loc2repair run-baseline \
  --task-file "$HOME/nir/stage-aware-routing/data/pilot/protocol/tasks/verified_test.jsonl" \
  --dataset-root "$HOME/nir/stage-aware-routing/data/pilot/exported_swebench_verified" \
  --runs-dir "$HOME/nir/stage-aware-routing/runs/pilot/gemma4/baseline" \
  --out "$HOME/nir/stage-aware-routing/runs/pilot/gemma4/baseline/baseline.jsonl" \
  --workers 1 --timeout 1800 --resume \
  || { echo "BLOCKED or FAILED"; false; }
```

## 4. Scoring (VPN off, no credentials needed, new terminal)

Build the harness inputs, check the dataset revision and every required image, then score. The harness's own image pull failed silently on this setup, so images are pulled and checked by name first.

```bash
bash <<'BASH'
set -eo pipefail
source "$HOME/nir/loc2repair/.venv/bin/activate"
set -u
cd "$HOME/nir/stage-aware-routing"

python3 - <<'PY'
from huggingface_hub import HfApi
expected = "78f471bf655a3137b2e8a75af1501690ec009ec3"
actual = HfApi().dataset_info("SWE-bench/SWE-bench_Verified").sha
if actual != expected:
    raise SystemExit(f"STOP: Dataset revision mismatch: {actual}")
print("Dataset revision verified.")
PY

HARNESS="$HOME/nir/stage-aware-routing/runs/pilot/harness"
mkdir -p "$HARNESS"

loc2repair build-harness-predictions \
  --runs-dir "$HOME/nir/stage-aware-routing/runs/pilot/qwen38/baseline" \
  --out "$HARNESS/qwen38.predictions.jsonl" \
  --model-name-or-path qwen3.8

loc2repair build-harness-predictions \
  --runs-dir "$HOME/nir/stage-aware-routing/runs/pilot/gemma4/baseline" \
  --out "$HARNESS/gemma4.predictions.jsonl" \
  --model-name-or-path gemma-4-26B-A4B-it

ids=$(python3 - <<'PY'
import json
tasks = json.load(open("docs/pilot_tasks.json"))["tasks"]
ids = [t["instance_id"] for t in tasks]
assert len(ids) == 20
assert len(set(ids)) == 20
print(" ".join(ids))
PY
)

cd "$HOME/nir/stage-aware-routing/runs/pilot/harness"
test -s qwen38.predictions.jsonl
test -s gemma4.predictions.jsonl

for id in $ids; do
    img="swebench/sweb.eval.x86_64.${id//__/_1776_}:latest"
    docker pull -q "$img" >/dev/null
    docker image inspect "$img" >/dev/null
done
echo "All 20 required Docker images verified."

python -m swebench.harness.run_evaluation --dataset_name SWE-bench/SWE-bench_Verified \
  --split test --predictions_path qwen38.predictions.jsonl --max_workers 1 \
  --cache_level env --clean false --run_id pilot-qwen38

python -m swebench.harness.run_evaluation --dataset_name SWE-bench/SWE-bench_Verified \
  --split test --predictions_path gemma4.predictions.jsonl --max_workers 1 \
  --cache_level env --clean false --run_id pilot-gemma4
BASH
```

Runs that timed out are not scored and count as unresolved (decision D8).

## 5. Results

```bash
cd ~/nir/stage-aware-routing
python3 scripts/pilot_results.py     # writes docs/pilot_results.md
```
