"""Tests for the analysis scripts, using small synthetic inputs in a temporary folder."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True)


def diff(*files):
    parts = []
    for path, kind in files:
        parts.append(f"diff --git a/{path} b/{path}")
        if kind == "NEW":
            parts.append("new file mode 100644")
        if kind == "DEL":
            parts.append("deleted file mode 100644")
        parts.append(f"+++ b/{path}")
    return "\n".join(parts) + "\n"


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def row(iid, status="ok", sec=10, steps=3, inp=1000, out=50, patch=""):
    return {"instance_id": iid, "status": status, "elapsed_sec": sec, "predicted_diff": patch,
            "repair_usage": {"agent_steps": steps, "input_tokens": inp, "output_tokens": out}}


def test_list_patch_files_counts(tmp_path):
    f = tmp_path / "run.jsonl"
    write_jsonl(f, [row("repo__a-1", patch=diff(("src/a.py", "MOD"), ("new.py", "NEW"), ("old.py", "DEL")))])
    r = run("list_patch_files.py", f)
    assert r.returncode == 0
    assert "repo__a-1  ok  MOD=1 NEW=1 DEL=1" in r.stdout
    assert "Tasks that change at least one existing file: 1/1" in r.stdout


def test_summarize_runs_values(tmp_path):
    f = tmp_path / "run.jsonl"
    write_jsonl(f, [
        row("repo__a-1", sec=10, steps=3, inp=1000, out=50, patch=diff(("a.py", "MOD"), ("b.py", "MOD"))),
        row("repo__b-2", status="timeout", sec=20, steps=7, inp=2000, out=80, patch=diff(("c.py", "MOD"))),
    ])
    r = run("summarize_runs.py", f)
    assert r.returncode == 0
    lines = {l.split()[0]: l.split() for l in r.stdout.splitlines() if l.startswith("repo__")}
    assert lines["repo__a-1"][1:7] == ["ok", "10", "3", "1000", "50", "2"]
    assert lines["repo__b-2"][1:7] == ["timeout", "20", "7", "2000", "80", "1"]
    assert "tasks: 2" in r.stdout


def pilot_inputs(tmp_path, gemma_t1_out=0):
    qr, qrep = tmp_path / "q.jsonl", tmp_path / "q.json"
    gr, grep_ = tmp_path / "g.jsonl", tmp_path / "g.json"
    write_jsonl(qr, [row("t1", inp=1_000_000, out=0), row("t2", inp=2_000_000, out=0)])
    write_jsonl(gr, [row("t1", inp=100_000, out=gemma_t1_out), row("t2", inp=300_000, out=0)])
    qrep.write_text(json.dumps({"resolved_ids": ["t1", "t2"], "unresolved_ids": [], "error_ids": []}))
    grep_.write_text(json.dumps({"resolved_ids": ["t1"], "unresolved_ids": ["t2"], "error_ids": []}))
    return ["--qwen-run", qr, "--qwen-report", qrep, "--gemma-run", gr, "--gemma-report", grep_,
            "--expected-tasks", 2, "--out", tmp_path / "out.md"]


def test_pilot_results_oracles(tmp_path):
    r = run("pilot_results.py", *pilot_inputs(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "Success oracle (solved by at least one model): 2/2." in r.stdout
    assert "| Always Qwen | 2 |" in r.stdout and "| 3.0 |" in r.stdout
    assert "| Token-oracle (fewest tokens among models that solve) | 2 |" in r.stdout
    token_line = [l for l in r.stdout.splitlines() if l.startswith("| Token-oracle")][0]
    assert token_line.endswith("| 2.1 |")
    assert (tmp_path / "out.md").exists()


def test_pilot_results_stops_on_missing_tokens(tmp_path):
    args = pilot_inputs(tmp_path)
    g = tmp_path / "g.jsonl"
    rows = [json.loads(l) for l in g.read_text().splitlines()]
    del rows[0]["repair_usage"]["output_tokens"]
    write_jsonl(g, rows)
    r = run("pilot_results.py", *args)
    assert r.returncode != 0
    assert "Missing data" in r.stdout + r.stderr


def test_pilot_results_stops_on_wrong_task_count(tmp_path):
    args = pilot_inputs(tmp_path)
    args[args.index("--expected-tasks") + 1] = 3
    r = run("pilot_results.py", *args)
    assert r.returncode != 0
