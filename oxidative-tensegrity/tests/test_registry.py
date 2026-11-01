"""Tests for the shared experiment registry (experiments/registry.py).

Covers: add, claim (ownership + transitions), verify (the different-solver
rule), refute, list/show, and the negative paths. All tests run against a
throwaway DB in tmp_path — never experiments/registry.db.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
import registry  # noqa: E402


@pytest.fixture()
def conn(tmp_path):
    return registry.connect(str(tmp_path / "registry.db"))


def _add_done(conn, exp_id="exp-1", calc="MACE-OFF MLIP stretch scan", **extra):
    return registry.add_experiment(
        conn, exp_id, "test hypothesis",
        params={"calculation": calc, **extra.pop("params_extra", {})},
        seeds=[0, 1, 2], status="done", code_version="deadbeef",
        result_location="results/x/", **extra,
    )


# ------------------------------------------------------------------ add

def test_add_defaults(conn):
    rec = registry.add_experiment(conn, "e1", "Hypothesis one", calc="solver A")
    assert rec["status"] == "proposed"
    assert rec["validation_status"] == "unvalidated"
    assert rec["validation_method"] is None
    assert rec["claimed_by"] is None
    assert rec["verified_by"] is None
    assert rec["seeds"] == []
    assert rec["params"]["calculation"] == "solver A"
    assert rec["created_at"] and rec["updated_at"]


def test_add_duplicate_id_rejected(conn):
    registry.add_experiment(conn, "e1", "h1")
    with pytest.raises(registry.RegistryError, match="already exists"):
        registry.add_experiment(conn, "e1", "h2")


def test_add_rejects_bad_status_and_params(conn):
    with pytest.raises(registry.RegistryError, match="invalid status"):
        registry.add_experiment(conn, "e1", "h", status="bogus")
    with pytest.raises(registry.RegistryError, match="JSON"):
        registry.add_experiment(conn, "e2", "h", params={"x": {1, 2}})  # set inside
    with pytest.raises(registry.RegistryError, match="JSON"):
        registry.add_experiment(conn, "e3", "h", seeds=[{1, 2}])


def test_add_requires_hypothesis(conn):
    with pytest.raises(registry.RegistryError, match="hypothesis"):
        registry.add_experiment(conn, "e1", "   ")


def test_seeds_roundtrip(conn):
    registry.add_experiment(conn, "e1", "h", seeds=[3, 7, 11])
    assert registry.show_experiment(conn, "e1")["seeds"] == [3, 7, 11]


# ------------------------------------------------------------------ claim

def test_claim_proposed_to_claimed(conn):
    registry.add_experiment(conn, "e1", "h")
    rec = registry.claim_experiment(conn, "e1", "Codex, GCP cpu32")
    assert rec["status"] == "claimed"
    assert rec["claimed_by"] == "Codex, GCP cpu32"
    assert rec["claimed_at"] is not None


def test_claim_blocked_when_claimed_by_other(conn):
    registry.add_experiment(conn, "e1", "h")
    registry.claim_experiment(conn, "e1", "Agent A, VM x")
    with pytest.raises(registry.RegistryError, match="already claimed by 'Agent A, VM x'"):
        registry.claim_experiment(conn, "e1", "Agent B, VM y")


def test_claim_same_agent_can_advance(conn):
    registry.add_experiment(conn, "e1", "h")
    registry.claim_experiment(conn, "e1", "Agent A")
    rec = registry.claim_experiment(conn, "e1", "Agent A", to_status="running")
    assert rec["status"] == "running"
    rec = registry.claim_experiment(conn, "e1", "Agent A", to_status="done")
    assert rec["status"] == "done"


def test_claim_invalid_transition(conn):
    registry.add_experiment(conn, "e1", "h")
    with pytest.raises(registry.RegistryError, match="cannot claim-move"):
        registry.claim_experiment(conn, "e1", "Agent A", to_status="done")  # proposed -> done
    with pytest.raises(registry.RegistryError, match="terminal"):
        registry.add_experiment(conn, "e2", "h", status="verified")
        registry.claim_experiment(conn, "e2", "Agent A")


def test_claim_unknown_id(conn):
    with pytest.raises(registry.RegistryError, match="no such experiment"):
        registry.claim_experiment(conn, "nope", "Agent A")


# ------------------------------------------------------------------ verify

def test_verify_requires_done(conn):
    registry.add_experiment(conn, "e1", "h", calc="solver A")
    registry.claim_experiment(conn, "e1", "Agent A")
    with pytest.raises(registry.RegistryError, match="requires status 'done'"):
        registry.verify_experiment(conn, "e1", "solver B", "method")


def test_verify_requires_original_calculation_recorded(conn):
    registry.add_experiment(conn, "e1", "h", params={}, status="done")
    with pytest.raises(registry.RegistryError, match=r"params\['calculation'\]"):
        registry.verify_experiment(conn, "e1", "PM7 (MOPAC)", "peak force")


def test_verify_rejects_same_solver(conn):
    _add_done(conn, calc="ALCHEMI two-MLIP scan: MACE-OFF and MACE-MP")
    with pytest.raises(registry.RegistryError, match="DIFFERENT calculation/solver"):
        registry.verify_experiment(conn, "exp-1", "MACE-OFF", "same model again")
    with pytest.raises(registry.RegistryError, match="DIFFERENT calculation/solver"):
        registry.verify_experiment(conn, "exp-1", "ALCHEMI two-MLIP scan MACE-OFF MACE-MP",
                                  "same solver, reworded")


def test_verify_requires_verifier_and_method(conn):
    _add_done(conn)
    with pytest.raises(registry.RegistryError, match="--verifier"):
        registry.verify_experiment(conn, "exp-1", "  ", "method")
    with pytest.raises(registry.RegistryError, match="--method"):
        registry.verify_experiment(conn, "exp-1", "PM7 (MOPAC)", " ")


def test_verify_success_and_fields(conn):
    _add_done(conn)
    rec = registry.verify_experiment(
        conn, "exp-1", "PM7 (MOPAC 23.2.5)",
        "peak force Spearman 0.95-0.98; k_rel NOT verified", by="Claude Code",
    )
    assert rec["status"] == "verified"
    assert rec["validation_status"] == "independently_verified"
    assert rec["validation_method"].startswith("PM7 (MOPAC 23.2.5)")
    assert "k_rel NOT verified" in rec["validation_method"]
    assert rec["verified_by"] == "Claude Code"
    assert rec["verified_at"] is not None


def test_verify_is_terminal(conn):
    _add_done(conn)
    registry.verify_experiment(conn, "exp-1", "PM7 (MOPAC)", "peak force")
    with pytest.raises(registry.RegistryError, match="requires status 'done'"):
        registry.verify_experiment(conn, "exp-1", "DFTB", "again")


# ------------------------------------------------------------------ refute

def test_refute_records_negative_result(conn):
    _add_done(conn)
    rec = registry.refute_experiment(conn, "exp-1", "all 9/9 runs hit the bound", by="Agent A")
    assert rec["status"] == "refuted"
    assert rec["validation_status"] == "refuted"
    assert rec["validation_method"].startswith("all 9/9")
    assert rec["verified_by"] == "Agent A"


def test_refute_blocked_from_proposed(conn):
    registry.add_experiment(conn, "e1", "h")
    with pytest.raises(registry.RegistryError, match="requires status 'done' or 'running'"):
        registry.refute_experiment(conn, "e1", "reason")


def test_refute_blocked_after_verify(conn):
    _add_done(conn)
    registry.verify_experiment(conn, "exp-1", "PM7 (MOPAC)", "peak force")
    with pytest.raises(registry.RegistryError, match="requires status 'done' or 'running'"):
        registry.refute_experiment(conn, "exp-1", "reason")


# ------------------------------------------------------------------ list / show / CLI

def test_list_filters_and_show_roundtrip(conn):
    registry.add_experiment(conn, "a", "h1", calc="s")
    registry.add_experiment(conn, "b", "h2", status="done")
    registry.add_experiment(conn, "c", "h3", status="refuted")
    assert [r["id"] for r in registry.list_experiments(conn)] == ["a", "b", "c"]
    assert [r["id"] for r in registry.list_experiments(conn, status="done")] == ["b"]
    rec = registry.show_experiment(conn, "b")
    assert rec["hypothesis"] == "h2"
    assert rec["params"] == {}
    with pytest.raises(registry.RegistryError, match="no such experiment"):
        registry.show_experiment(conn, "zzz")


def test_cli_verify_enforces_rule(tmp_path, capsys):
    db = str(tmp_path / "cli.db")
    argv_add = ["--db", db, "add", "--id", "x1", "--hypothesis", "h",
                "--calc", "MACE-OFF MLIP", "--params", '{"seed": 7}', "--status", "done"]
    assert registry.main(argv_add) == 0
    # same solver -> rejected with exit code 2
    assert registry.main(["--db", db, "verify", "x1", "--verifier", "MACE-OFF",
                          "--method", "same"]) == 2
    err = capsys.readouterr().err
    assert "DIFFERENT calculation/solver" in err
    # different solver -> accepted
    assert registry.main(["--db", db, "verify", "x1", "--verifier", "PM7 (MOPAC 23.2.5)",
                           "--method", "peak force", "--by", "test"]) == 0
    assert registry.main(["--db", db, "list", "--validation-status",
                          "independently_verified"]) == 0
    out = capsys.readouterr().out
    assert "x1" in out and "independently_verified" in out
    # params round-trip through CLI
    assert registry.main(["--db", db, "show", "x1"]) == 0
    assert '"seed": 7' in capsys.readouterr().out
