#!/usr/bin/env python3
"""Shared experiment registry for the oxidative-tensegrity project.

stdlib only (sqlite3, argparse, json, subprocess, datetime).

Project rules encoded here:
  * Agents claim experiments through this registry so no two sessions
    duplicate the same calculation.
  * A finding becomes reusable because ANOTHER calculation verifies it,
    not because several agents agree: `verify` refuses to move an
    experiment to status `verified` unless `params["calculation"]`
    records the original calculation and the named verifying
    solver/calculation is distinct from it.
  * Negative results are first-class citizens: `refute` records them.

CLI (run from the repo folder, i.e. Science/oxidative-tensegrity):
  python experiments/registry.py add --id ID --hypothesis "..." \
      [--calc "original calculation"] [--params JSON] [--seeds JSON] \
      [--status proposed] [--code-version SHA] [--result-location PATH]
  python experiments/registry.py claim ID --by "agent / instance" [--status claimed|running|done]
  python experiments/registry.py verify ID --verifier "solver (version)" --method "what it verified" [--by "agent"]
  python experiments/registry.py refute ID --reason "why the hypothesis is refuted" [--by "agent"]
  python experiments/registry.py list [--status S] [--validation-status V]
  python experiments/registry.py show ID

DB location: experiments/registry.db next to this file, or $OXT_REGISTRY,
or --db PATH (tests use a temp path).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

STATUSES = ("proposed", "claimed", "running", "done", "verified", "refuted")
VALIDATION_STATUSES = ("unvalidated", "independently_verified", "refuted")

# Lifecycle transitions enforced by the CLI.
CLAIM_TRANSITIONS = {
    ("proposed", "claimed"),
    ("claimed", "running"),
    ("claimed", "done"),
    ("running", "done"),
}
VERIFY_TRANSITIONS = {("done", "verified")}
REFUTE_TRANSITIONS = {("done", "refuted"), ("running", "refuted")}

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id                 TEXT PRIMARY KEY,
    hypothesis         TEXT NOT NULL,
    code_version       TEXT,                -- git sha of the repo at run time
    params             TEXT NOT NULL DEFAULT '{}',  -- JSON object; params["calculation"] = original solver
    seeds              TEXT NOT NULL DEFAULT '[]',  -- JSON list
    status             TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed','claimed','running','done','verified','refuted')),
    validation_status  TEXT NOT NULL DEFAULT 'unvalidated'
        CHECK (validation_status IN ('unvalidated','independently_verified','refuted')),
    validation_method  TEXT,                -- free text: which separate calculation verified it
    result_location    TEXT,                -- path (repo-relative or absolute)
    claimed_by         TEXT,
    verified_by        TEXT,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    claimed_at         TEXT,
    verified_at        TEXT
);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_validation ON experiments(validation_status);
"""


class RegistryError(Exception):
    """Expected, user-facing registry failure (bad transition, duplicate id, ...)."""


# ---------------------------------------------------------------- utilities

def default_db_path() -> str:
    env = os.environ.get("OXT_REGISTRY")
    if env:
        return env
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.db")


def connect(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or default_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git_sha() -> str | None:
    """Best-effort HEAD sha of the enclosing git repo at run time."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root,
            capture_output=True, text=True, timeout=10,
        )
        sha = out.stdout.strip()
        if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{7,40}", sha):
            return sha
    except Exception:
        pass
    return None


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _calc_tokens(params: dict) -> set:
    """Tokens of the ORIGINAL calculation/solver, from params['calculation'] (or 'solver')."""
    tokens: set = set()
    for key in ("calculation", "solver"):
        val = params.get(key)
        if isinstance(val, str):
            tokens |= _tokens(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    tokens |= _tokens(item)
    return tokens


def _get(conn: sqlite3.Connection, exp_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM experiments WHERE id = ?", (exp_id,)
    ).fetchone()
    if row is None:
        raise RegistryError(f"no such experiment: '{exp_id}'")
    return row


def _check_json(value, what: str):
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise RegistryError(f"{what} is not JSON-serializable: {exc}")


# ---------------------------------------------------------------- API

def add_experiment(
    conn: sqlite3.Connection,
    exp_id: str,
    hypothesis: str,
    params: dict | None = None,
    seeds: list | None = None,
    status: str = "proposed",
    code_version: str | None = None,
    result_location: str | None = None,
    calc: str | None = None,
) -> dict:
    if not exp_id or not exp_id.strip():
        raise RegistryError("experiment id is required")
    if not hypothesis or not hypothesis.strip():
        raise RegistryError("hypothesis is required")
    if status not in STATUSES:
        raise RegistryError(f"invalid status '{status}'; allowed: {', '.join(STATUSES)}")
    params = dict(params or {})
    if calc and "calculation" not in params:
        params["calculation"] = calc
    seeds = list(seeds or [])
    _check_json(params, "params")
    _check_json(seeds, "seeds")
    if _get_or_none(conn, exp_id) is not None:
        raise RegistryError(f"experiment '{exp_id}' already exists")
    ts = _now()
    conn.execute(
        "INSERT INTO experiments (id, hypothesis, code_version, params, seeds, status,"
        " validation_status, validation_method, result_location, claimed_by, verified_by,"
        " created_at, updated_at, claimed_at, verified_at)"
        " VALUES (?, ?, ?, ?, ?, ?, 'unvalidated', NULL, ?, NULL, NULL, ?, ?, NULL, NULL)",
        (exp_id, hypothesis, code_version, json.dumps(params), json.dumps(seeds),
         status, result_location, ts, ts),
    )
    conn.commit()
    return show_experiment(conn, exp_id)


def _get_or_none(conn, exp_id):
    return conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()


def claim_experiment(
    conn: sqlite3.Connection, exp_id: str, by: str, to_status: str | None = None
) -> dict:
    row = _get(conn, exp_id)
    if not by or not by.strip():
        raise RegistryError("--by is required (who/what is claiming)")
    if row["status"] in ("verified", "refuted"):
        raise RegistryError(
            f"experiment '{exp_id}' is terminal ({row['status']}); cannot claim"
        )
    if row["claimed_by"] and row["claimed_by"] != by:
        raise RegistryError(
            f"experiment '{exp_id}' is already claimed by '{row['claimed_by']}' "
            f"(status {row['status']}); do not duplicate work — check with them first"
        )
    target = to_status or "claimed"
    if (row["status"], target) not in CLAIM_TRANSITIONS:
        allowed = ", ".join(f"{a}->{b}" for a, b in sorted(CLAIM_TRANSITIONS))
        raise RegistryError(
            f"cannot claim-move '{exp_id}' {row['status']} -> {target}; "
            f"allowed claim transitions: {allowed}"
        )
    sets, vals = ["status = ?", "updated_at = ?", "claimed_by = ?"], [target, _now(), by]
    if row["claimed_at"] is None:
        sets.append("claimed_at = ?")
        vals.append(_now())
    vals.append(exp_id)
    conn.execute(f"UPDATE experiments SET {', '.join(sets)} WHERE id = ?", vals)
    conn.commit()
    return show_experiment(conn, exp_id)


def verify_experiment(
    conn: sqlite3.Connection, exp_id: str, verifier: str, method: str, by: str | None = None
) -> dict:
    row = _get(conn, exp_id)
    if (row["status"], "verified") not in VERIFY_TRANSITIONS:
        raise RegistryError(
            f"verify requires status 'done' (current status of '{exp_id}': '{row['status']}'); "
            "mark the run finished first"
        )
    if not verifier or not verifier.strip():
        raise RegistryError(
            "--verifier is required: name the calculation/solver that verified the finding"
        )
    if not method or not method.strip():
        raise RegistryError(
            "--method is required: describe what the separate calculation verified "
            "(and what it did not)"
        )
    params = json.loads(row["params"] or "{}")
    orig_tokens = _calc_tokens(params)
    if not orig_tokens:
        raise RegistryError(
            f"params['calculation'] of '{exp_id}' does not record the original "
            "calculation/solver; add it before verifying so the registry can enforce "
            "that the verifier is a DIFFERENT calculation"
        )
    verifier_tokens = _tokens(verifier)
    if not (verifier_tokens - orig_tokens):
        raise RegistryError(
            "verification must name a DIFFERENT calculation/solver than the original "
            f"(original: '{params.get('calculation', params.get('solver'))}'). "
            f"'{verifier}' is not distinct. Several agents agreeing is not verification — "
            "find a separate calculation that reproduces (or bounds) the finding."
        )
    method_text = f"{verifier} — {method}"
    conn.execute(
        "UPDATE experiments SET status = 'verified', validation_status = 'independently_verified',"
        " validation_method = ?, verified_by = ?, verified_at = ?, updated_at = ? WHERE id = ?",
        (method_text, by or "unknown", _now(), _now(), exp_id),
    )
    conn.commit()
    return show_experiment(conn, exp_id)


def refute_experiment(
    conn: sqlite3.Connection, exp_id: str, reason: str, by: str | None = None
) -> dict:
    row = _get(conn, exp_id)
    if (row["status"], "refuted") not in REFUTE_TRANSITIONS:
        raise RegistryError(
            f"refute requires status 'done' or 'running' (current: '{row['status']}')"
        )
    if not reason or not reason.strip():
        raise RegistryError("--reason is required: record why the hypothesis is refuted")
    conn.execute(
        "UPDATE experiments SET status = 'refuted', validation_status = 'refuted',"
        " validation_method = ?, verified_by = ?, verified_at = ?, updated_at = ? WHERE id = ?",
        (reason, by or "unknown", _now(), _now(), exp_id),
    )
    conn.commit()
    return show_experiment(conn, exp_id)


def list_experiments(
    conn: sqlite3.Connection, status: str | None = None, validation_status: str | None = None
) -> list[dict]:
    sql = "SELECT * FROM experiments"
    where, vals = [], []
    if status:
        if status not in STATUSES:
            raise RegistryError(f"invalid status '{status}'")
        where.append("status = ?")
        vals.append(status)
    if validation_status:
        if validation_status not in VALIDATION_STATUSES:
            raise RegistryError(f"invalid validation_status '{validation_status}'")
        where.append("validation_status = ?")
        vals.append(validation_status)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at, id"
    return [dict(r) for r in conn.execute(sql, vals)]


def show_experiment(conn: sqlite3.Connection, exp_id: str) -> dict:
    row = _get(conn, exp_id)
    rec = dict(row)
    rec["params"] = json.loads(rec["params"] or "{}")
    rec["seeds"] = json.loads(rec["seeds"] or "[]")
    return rec


# ---------------------------------------------------------------- CLI

def _fmt_table(records: list[dict]) -> str:
    cols = ("id", "status", "validation_status", "claimed_by", "hypothesis")
    rows = []
    for r in records:
        h = (r.get("hypothesis") or "").replace("\n", " ")
        if len(h) > 70:
            h = h[:67] + "..."
        rows.append([r.get("id") or "", r.get("status") or "",
                     r.get("validation_status") or "", r.get("claimed_by") or "", h])
    if not rows:
        return "(no experiments)"
    widths = [max(len(str(r[i])) for r in rows + [[c.title() for c in cols]]) for i, c in enumerate(cols)]
    out = []
    header = "  ".join(c.title().ljust(w) for c, w in zip(cols, widths))
    out.append(header)
    out.append("  ".join("-" * w for w in widths))
    for r in rows:
        out.append("  ".join(str(v).ljust(w) for v, w in zip(r, widths)))
    return "\n".join(out)


def _print_record(rec: dict):
    p = rec["params"]
    print(f"id:                 {rec['id']}")
    print(f"hypothesis:         {rec['hypothesis']}")
    print(f"code_version:       {rec['code_version']}")
    print(f"params:             {json.dumps(p, sort_keys=True)}")
    print(f"seeds:              {json.dumps(rec['seeds'])}")
    print(f"status:             {rec['status']}")
    print(f"validation_status:  {rec['validation_status']}")
    print(f"validation_method:  {rec['validation_method']}")
    print(f"result_location:    {rec['result_location']}")
    print(f"claimed_by:         {rec['claimed_by']}")
    print(f"verified_by:        {rec['verified_by']}")
    print(f"created_at:         {rec['created_at']}")
    print(f"updated_at:         {rec['updated_at']}")
    print(f"claimed_at:         {rec['claimed_at']}")
    print(f"verified_at:        {rec['verified_at']}")


def _json_arg(text: str, what: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"--{what} is not valid JSON: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="registry.py",
        description="Shared experiment registry (oxidative-tensegrity).",
    )
    parser.add_argument("--db", default=None, help="registry DB path (default: experiments/registry.db or $OXT_REGISTRY)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="register a new experiment")
    p_add.add_argument("--id", required=True, help="short slug, e.g. b1-alchemi-two-mlip")
    p_add.add_argument("--hypothesis", required=True)
    p_add.add_argument("--calc", default=None,
                       help="original calculation/solver (stored as params['calculation']; required before verify)")
    p_add.add_argument("--params", default=None, help="JSON object of run parameters/assumptions")
    p_add.add_argument("--seeds", default=None, help="JSON list of RNG seeds")
    p_add.add_argument("--status", default="proposed", choices=STATUSES,
                       help="lifecycle status (use non-default only for backfill)")
    p_add.add_argument("--code-version", default=None,
                       help="git sha at run time (default: HEAD of the enclosing repo, if any)")
    p_add.add_argument("--result-location", default=None)

    p_claim = sub.add_parser("claim", help="claim an experiment / advance its run status")
    p_claim.add_argument("id")
    p_claim.add_argument("--by", required=True, help="agent + machine/instance, e.g. 'Codex, GCP cpu32'")
    p_claim.add_argument("--status", default=None, choices=["claimed", "running", "done"])

    p_verify = sub.add_parser("verify", help="mark done -> verified via a DIFFERENT calculation")
    p_verify.add_argument("id")
    p_verify.add_argument("--verifier", required=True,
                          help="the separate calculation/solver that verified the finding, e.g. 'PM7 (MOPAC 23.2.5)'")
    p_verify.add_argument("--method", required=True,
                          help="what it verified, what it did not, and on which quantities")
    p_verify.add_argument("--by", default=None, help="who recorded the verification")

    p_refute = sub.add_parser("refute", help="record a refuted hypothesis / negative result")
    p_refute.add_argument("id")
    p_refute.add_argument("--reason", required=True)
    p_refute.add_argument("--by", default=None)

    p_list = sub.add_parser("list", help="list experiments")
    p_list.add_argument("--status", default=None, choices=STATUSES)
    p_list.add_argument("--validation-status", default=None, choices=VALIDATION_STATUSES)

    p_show = sub.add_parser("show", help="show one experiment in full")
    p_show.add_argument("id")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        conn = connect(args.db)
        if args.cmd == "add":
            params = _json_arg(args.params, "params") if args.params else {}
            if not isinstance(params, dict):
                raise RegistryError("--params must be a JSON object")
            seeds = _json_arg(args.seeds, "seeds") if args.seeds else []
            if not isinstance(seeds, list):
                raise RegistryError("--seeds must be a JSON list")
            rec = add_experiment(
                conn, args.id, args.hypothesis, params=params, seeds=seeds,
                status=args.status,
                code_version=args.code_version if args.code_version is not None else git_sha(),
                result_location=args.result_location, calc=args.calc,
            )
            _print_record(rec)
        elif args.cmd == "claim":
            _print_record(claim_experiment(conn, args.id, args.by, args.status))
        elif args.cmd == "verify":
            _print_record(verify_experiment(conn, args.id, args.verifier, args.method, args.by))
        elif args.cmd == "refute":
            _print_record(refute_experiment(conn, args.id, args.reason, args.by))
        elif args.cmd == "list":
            recs = list_experiments(conn, args.status, args.validation_status)
            print(_fmt_table(recs))
            print(f"({len(recs)} experiment{'s' if len(recs) != 1 else ''})")
        elif args.cmd == "show":
            _print_record(show_experiment(conn, args.id))
        return 0
    except RegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
