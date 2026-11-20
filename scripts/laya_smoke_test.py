"""Minimal Laya check with synthetic reports: status, time, raw reply."""
import json
import os
import time
import urllib.error
import urllib.request

URL = os.environ["LAYA_URL"]
KEY = os.environ["LAYA_API_KEY"]

BASE = (
    "Issue: a date parsing helper returns the wrong month for some inputs. "
    "Files likely involved: utils/dates.py. The fix looks small and local. "
)
REPORTS = {
    "small": BASE,
    "medium": BASE * 10,
    "large": BASE * 60,
}
QUESTION = {
    "model": {
        "type": "choice",
        "instructions": "Which repair model is the best fit for this task?",
        "criteria": {
            "gemma": "Faster, lower-cost model. Suits small, local fixes.",
            "qwen": "Slower, stronger model. Suits fixes that need deeper reasoning or touch several files.",
        },
    }
}

for name, report in REPORTS.items():
    body = json.dumps({"state": {"request": report}, "questions": QUESTION}).encode()
    req = urllib.request.Request(
        URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status, reply = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, reply = e.code, e.read().decode()
    except Exception as e:
        status, reply = "FAIL", type(e).__name__
    print(f"\n[{name}] words={len(report.split())} status={status} time={time.time() - start:.1f}s")
    print(reply[:1500])
