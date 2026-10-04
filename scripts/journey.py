#!/usr/bin/env python3
"""The main journey (MISSION.md Gate 3), driven over HTTP like a real founder. Stdlib only.

Usage: python3 scripts/journey.py [BASE_URL] [FIXTURE]
  BASE_URL defaults to http://localhost:3000; FIXTURE defaults to real_pain.
Prints APP_STARTED when health is ok, and E2E_PASSED steps=9 when every step passes.
Real Jev and OpenAI are called: never point this at a mocked analyzer (FACTORY_RULES.md §2 rule 4).
"""

import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000").rstrip("/")
FIXTURE = sys.argv[2] if len(sys.argv) > 2 else "real_pain"
FIXTURES = Path(__file__).resolve().parent.parent / "services/analyzer/fixtures"
IDEA = "WhatsApp bot that takes restaurant reservations"
TIMEOUT_S = 120

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers={"content-type": "application/json"})
    try:
        with opener.open(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def step(n: int, ok: bool, what: str) -> None:
    print(f"step {n}: {'ok  ' if ok else 'FAIL'} {what}")
    if not ok:
        print("E2E_FAILED")
        sys.exit(1)


transcript = (FIXTURES / f"{FIXTURE}.txt").read_text()
labels = json.loads((FIXTURES / f"{FIXTURE}.labels.json").read_text())

status, health = call("GET", "/api/health")
step(1, status == 200 and health == {"status": "ok", "db": "ok", "analyzer": "ok"}, f"health {health}")
print("APP_STARTED")

status, idea = call("POST", "/api/ideas", {"one_liner": IDEA})
step(2, status == 201 and "id" in idea, "create idea")

status, created = call("POST", "/api/interviews", {"idea_id": idea["id"], "transcript": transcript, "kind": "interview"})
step(3, status == 202 and "id" in created, f"submit {FIXTURE}")

status, first = call("GET", f"/api/interviews/{created['id']}")
step(4, first.get("status") in ("processing", "done"), f"status shows {first.get('status')}")

started = time.monotonic()
while True:
    status, current = call("GET", f"/api/interviews/{created['id']}")
    if current.get("status") != "processing" or time.monotonic() - started > TIMEOUT_S:
        break
    time.sleep(2)
elapsed = time.monotonic() - started
step(5, current.get("status") == "done", f"done in {elapsed:.0f}s (error={current.get('error')})")

result = current["result"]
band = labels["score_band"]
score = result["score"]
in_band = score is not None and score > band.get("min_exclusive", -1) and score >= band.get("min_inclusive", 0) \
    and score < band.get("max_exclusive", 101) and score <= band.get("max_inclusive", 100)
step(6, result["verdict"] in labels["allowed_verdicts"] and in_band,
     f"verdict={result['verdict']} score={score} (allowed {labels['allowed_verdicts']}, band {band})")

real_quotes = [s["quote"] for s in result["statements"] if s["category"] in ("commitment", "past_pain")]
verbatim = all(s["quote"] in transcript for s in result["statements"])
needs_real = FIXTURE == "real_pain"
step(7, verbatim and (bool(real_quotes) or not needs_real), f"{len(real_quotes)} real-signal quotes, all verbatim={verbatim}")

step(8, len(result["next_questions"]) == 3, "exactly 3 next questions")

status, history = call("GET", f"/api/ideas/{idea['id']}")
listed = [i for i in history.get("interviews", []) if i["id"] == created["id"]]
step(9, bool(listed) and listed[0]["verdict"] == result["verdict"], "idea history lists it with the same verdict")

print(f"verdict={result['verdict']} score={score} confidence={result['verdict_confidence']}")
print("E2E_PASSED steps=9")
