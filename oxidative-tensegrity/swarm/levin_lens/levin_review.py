#!/usr/bin/env python3
"""Levin-lens and open-endedness reviewers over this project (Gemini API, stdlib only).

Never executes source files or model output; it only reads text, sends it to the Gemini API and saves replies.

  python3 levin_review.py --build OUT            # on the Mac: freeze the packet (OUT/packet.txt + manifest.json)
  python3 levin_review.py --run OUT --stage 1    # on the VM: stage-1 reviewers in parallel
  python3 levin_review.py --run OUT --stage 2    # on the VM: adversarial reviewer, reads stage-1 replies

The key is read from ~/.gemini.key on the machine that runs --run; it is never printed or written out.
Raw replies go to OUT/raw/ and stay local (swarm/work/ is not published).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
API = "https://generativelanguage.googleapis.com/v1beta/models/"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(b: bytes):
    return hashlib.sha256(b).hexdigest()


def build(out: Path, roles: dict):
    out.mkdir(parents=True, exist_ok=True)
    parts, files = [], []
    for rel in roles["packet_files"]:
        b = (ROOT / rel).read_bytes()
        files.append({"name": rel, "sha256": sha(b), "bytes": len(b)})
        parts.append(f"\n\n===== FILE: {rel} =====\n{b.decode()}")
    packet = "".join(parts)
    (out / "packet.txt").write_text(packet)
    (out / "roles.json").write_text(json.dumps(roles, indent=1))
    (out / "manifest.json").write_text(json.dumps(
        {"built_at": now(), "files": files, "packet_sha256": sha(packet.encode()), "chars": len(packet)}, indent=1))
    print(f"packet: {len(files)} files, {len(packet)} chars")


def call(model, system, user, key, max_tokens, thinking):
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json",
                                 "thinkingConfig": {"thinkingLevel": thinking}}}
    req = urllib.request.Request(API + model + ":generateContent", data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=900) as r:
        return json.loads(r.read().decode().replace(key, "[REDACTED]"))


def review(role, roles, packet, key, args, extra=""):
    system = roles["personas"][role["persona"]] + "\n\n" + roles["common"]
    user = (f"TASK ({role['id']}):\n{role['task']}\n\nOUTPUT SCHEMA:\n{roles['schema']}\n\n"
            f"PACKET (project files follow):{packet}{extra}")
    rec = {"role": role["id"], "persona": role["persona"], "model": args.model, "started_at": now(),
           "prompt_sha256": sha(user.encode())}
    raw = args.run / "raw"
    try:
        t0 = time.time()
        resp = call(args.model, system, user, key, args.max_tokens, args.thinking)
        rec["seconds"] = round(time.time() - t0, 1)
        text = "".join(p.get("text", "") for c in resp.get("candidates", [])
                       for p in c.get("content", {}).get("parts", []) if not p.get("thought"))
        rec["usage"] = resp.get("usageMetadata", {})
        rec["finish"] = [c.get("finishReason") for c in resp.get("candidates", [])]
        rec["modelVersion"] = resp.get("modelVersion")
        (raw / f"{role['id']}.response.json").write_text(json.dumps(resp, indent=1))
        try:
            parsed = json.loads(re.sub(r"^```(json)?|```$", "", text.strip()))
            (raw / f"{role['id']}.json").write_text(json.dumps(parsed, indent=1))
            rec["status"] = "ok"
            rec["bridges"] = len(parsed.get("bridges", []))
            rec["citations"] = len(parsed.get("citations", []))
        except json.JSONDecodeError as e:
            (raw / f"{role['id']}.txt").write_text(text)
            rec["status"] = f"unparsed ({e.msg})"
    except urllib.error.HTTPError as e:  # never log headers or body (could echo the request)
        rec["status"] = f"http {e.code}"
    except Exception as e:
        rec["status"] = f"error {type(e).__name__}"
    rec["finished_at"] = now()
    print(rec["role"], rec["status"], rec.get("seconds"), flush=True)
    return rec


def run(args):
    roles = json.loads((args.run / "roles.json").read_text())
    packet = (args.run / "packet.txt").read_text()
    kp = Path.home() / ".gemini.key"
    if kp.is_symlink() or not kp.is_file() or kp.stat().st_mode & 0o077:
        raise SystemExit("~/.gemini.key missing or not owner-only")
    key = kp.read_text().strip()
    (args.run / "raw").mkdir(exist_ok=True)
    todo = [r for r in roles["roles"] if r["stage"] == args.stage]
    extra = ""
    if args.stage == 2:
        for r in roles["roles"]:
            p = args.run / "raw" / f"{r['id']}.json"
            if r["stage"] == 1 and p.exists():
                extra += f"\n\n===== FIRST-ROUND REVIEW: {r['id']} ({r['persona']}) =====\n{p.read_text()}"
    with ThreadPoolExecutor(max_workers=3) as ex:
        recs = list(ex.map(lambda r: review(r, roles, packet, key, args, extra), todo))
    log = args.run / "run.json"
    prev = json.loads(log.read_text()) if log.exists() else {"runs": []}
    prev["runs"].append({"stage": args.stage, "model": args.model, "thinking": args.thinking,
                         "max_tokens": args.max_tokens, "automatic_retries": 0, "results": recs})
    log.write_text(json.dumps(prev, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", type=Path)
    g.add_argument("--run", type=Path)
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--model", default="gemini-4-argon")
    ap.add_argument("--thinking", default="high")
    ap.add_argument("--max-tokens", type=int, default=24576)
    ap.add_argument("--roles", type=Path, default=HERE / "roles.json", help="roles file used by --build")
    a = ap.parse_args()
    if not re.fullmatch(r"gemini-[A-Za-z0-9.-]+", a.model):
        raise SystemExit("bad model id")
    if a.build:
        build(a.build, json.loads(a.roles.read_text()))
    else:
        run(a)
