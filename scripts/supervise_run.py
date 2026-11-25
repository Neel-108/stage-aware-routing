"""Run a Loc2Repair command under a watchdog (D12).

Stops the run when the model server is unreachable for 3 checks in a row
(one model-list request every 60 s), when a result row has 0 agent steps,
on Ctrl+C, or if the watchdog itself fails. Fresh runs only, no resume.
At the end, all rows must be complete, match the task list exactly and have agent steps.
Prints overall progress only, no per-task IDs or statuses.
Usage: python scripts/supervise_run.py --out RUN/baseline.jsonl --tasks docs/main_tasks.json -- loc2repair run-baseline ...
"""
import argparse
import json
import os
import signal
import statistics
import subprocess
import sys
import time
from collections import Counter

from openai import OpenAI

IMAGE = "loc2repair-sandbox:latest"
TASK_DONE = [(300, 150), (300, 150), (300, 900), (300, 150), (300, 150), (300, 0)]
STOPPED = [(150, 100)] * 5


def now():
    return time.strftime("%H:%M:%S")


def beep(pattern):
    cmd = "; ".join(f"[console]::beep(1000,{d}); Start-Sleep -m {g}" for d, g in pattern)
    try:
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True)
    except FileNotFoundError:
        pass


def sandbox_containers():
    r = subprocess.run(["docker", "ps", "-q", "--filter", f"ancestor={IMAGE}"],
                       capture_output=True, text=True, check=True)
    return r.stdout.split()


def mount_sources(cid):
    r = subprocess.run(["docker", "inspect", cid, "--format", "{{range .Mounts}}{{.Source}}\n{{end}}"],
                       capture_output=True, text=True, check=True)
    return [s for s in r.stdout.splitlines() if s]


def in_run_dir(src, run_dir):
    src = os.path.normpath(src)
    return src == run_dir or src.startswith(run_dir + os.sep)


def run_containers(run_dir):
    """Sandbox containers with a mount that is exactly the run folder or inside it."""
    found = {}
    for cid in sandbox_containers():
        hits = [s for s in mount_sources(cid) if in_run_dir(s, run_dir)]
        if hits:
            found[cid] = hits[0]
    return found


def load(path, strict=False):
    """During the run a last line without a newline is skipped (still being written).
    With strict=True it is an error."""
    if not os.path.exists(path):
        return []
    text = open(path).read()
    lines = text.split("\n")
    if text and not text.endswith("\n"):
        if strict:
            raise ValueError("last line is incomplete")
        lines = lines[:-1]
    return [json.loads(line) for line in lines if line.strip()]


def steps(row):
    return (row.get("repair_usage") or {}).get("agent_steps")


def report(rows, total):
    c = Counter(r.get("status") for r in rows)
    sps = [r["elapsed_sec"] / steps(r) for r in rows if steps(r)]
    med = f"{statistics.median(sps):.1f}s/step" if sps else "n/a"
    hours = sum(r.get("elapsed_sec", 0) for r in rows) / 3600
    print(f"[{now()}] {len(rows)}/{total} done | ok {c.get('ok', 0)}, "
          f"timeout {c.get('timeout', 0)}, other {len(rows) - c.get('ok', 0) - c.get('timeout', 0)} | "
          f"median speed {med} | {hours:.2f} h", flush=True)


def final_check(out, expected):
    """Return a list of problems. Empty list means the run is complete and valid."""
    try:
        rows = load(out, strict=True)
    except Exception as ex:
        return [f"rows could not be read ({type(ex).__name__}: {ex})"]
    problems = []
    ids = [r.get("instance_id") for r in rows]
    if len(rows) != len(expected):
        problems.append(f"{len(rows)} rows, expected {len(expected)}")
    if len(set(ids)) != len(ids):
        problems.append("duplicate task IDs")
    if set(ids) != set(expected):
        problems.append("task IDs differ from the task list")
    bad = sum(1 for r in rows if not steps(r))
    if bad:
        problems.append(f"{bad} row(s) with 0 agent steps (D12)")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="baseline.jsonl written by the run")
    parser.add_argument("--tasks", required=True, help="task list JSON, for example docs/main_tasks.json")
    parser.add_argument("--check-every", type=int, default=60)
    parser.add_argument("--max-fails", type=int, default=3)
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        sys.exit("STOP: no run command given")

    expected = [t["instance_id"] for t in json.load(open(args.tasks))["tasks"]]
    total = len(expected)
    out = os.path.abspath(args.out)
    run_dir = os.path.normpath(os.path.dirname(out))
    if os.path.exists(out) and os.path.getsize(out) > 0:
        sys.exit("STOP: output file already has data. Fresh runs only, resume is not supported.")
    if os.path.isdir(run_dir) and os.listdir(run_dir):
        sys.exit("STOP: run folder is not empty. Fresh runs only, resume is not supported.")
    if sandbox_containers():
        sys.exit("STOP: a sandbox container is already running. Nothing started.")

    client = OpenAI(base_url=os.environ["REPAIR_BASE_URL"], api_key=os.environ["REPAIR_API_KEY"],
                    timeout=15, max_retries=0)
    proc = subprocess.Popen(cmd, start_new_session=True)
    print(f"[{now()}] started, run folder {run_dir}, {total} tasks", flush=True)
    seen, fails, last_check, reason, tracked = 0, 0, 0.0, None, set()
    warn_after = time.time() + 300
    try:
        while proc.poll() is None:
            time.sleep(5)
            for cid, src in run_containers(run_dir).items():
                if cid not in tracked:
                    tracked.add(cid)
                    print(f"[{now()}] tracking container {cid[:12]} (mount {src})", flush=True)
            if not tracked and time.time() > warn_after:
                print(f"[{now()}] WARNING: no sandbox container has a mount in the run folder. "
                      "On a stop, no container is stopped automatically.", flush=True)
                for cid in sandbox_containers():
                    print(f"    container {cid[:12]} mounts: {mount_sources(cid)}", flush=True)
                warn_after = float("inf")
            rows = load(out)
            if len(rows) > seen:
                new, seen = rows[seen:], len(rows)
                report(rows, total)
                if any(not steps(r) for r in new):
                    reason = "a result row has 0 agent steps (suspected infrastructure failure, D12)"
                    break
                beep(TASK_DONE)
            if time.time() - last_check >= args.check_every:
                last_check = time.time()
                try:
                    client.models.list()
                    fails = 0
                except Exception as ex:
                    fails += 1
                    print(f"[{now()}] server check failed ({type(ex).__name__}) {fails}/{args.max_fails}", flush=True)
                    if fails >= args.max_fails:
                        reason = f"model server unreachable for {fails} checks in a row (check VPN)"
                        break
    except KeyboardInterrupt:
        reason = "stopped by user (Ctrl+C)"
    except Exception as ex:
        reason = f"watchdog error ({type(ex).__name__}: {ex})"

    if reason is None:
        problems = final_check(out, expected)
        try:
            report(load(out), total)
        except Exception:
            pass
        if problems:
            print(f"[{now()}] FLAGGED: " + "; ".join(problems) + ". Investigate before scoring.", flush=True)
            beep(STOPPED)
            sys.exit(2)
        print(f"[{now()}] Run finished, exit code {proc.returncode}. "
              f"{total} complete rows, IDs match the task list, all have agent steps.", flush=True)
        sys.exit(proc.returncode)

    print(f"[{now()}] STOPPED: {reason}", flush=True)
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        ours = sorted(set(run_containers(run_dir)) | {c for c in tracked if c in sandbox_containers()})
        if ours:
            subprocess.run(["docker", "stop", *ours], capture_output=True, text=True, check=True)
            print(f"[{now()}] stopped container(s): {', '.join(c[:12] for c in ours)}", flush=True)
        left = sandbox_containers()
        if left:
            print(f"[{now()}] Sandbox containers still running, not stopped automatically: "
                  f"{', '.join(c[:12] for c in left)}. Check them by hand.", flush=True)
    except Exception as ex:
        print(f"[{now()}] container cleanup failed ({type(ex).__name__}). Check docker ps by hand.", flush=True)
    print("Run folder kept as is. Do not resume or delete before review.", flush=True)
    beep(STOPPED)
    sys.exit(2)


if __name__ == "__main__":
    main()
