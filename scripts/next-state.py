#!/usr/bin/env python3
"""Runtime for grounded-dev-loop. The model fills variables; this script picks the next state.

Guards are ordered. The first true guard wins. Unconditional edges are last.
A markdown copy of these edges is not the runtime.
"""
from __future__ import annotations

import json
import sys
from typing import Any

MODES = {"investigate", "debug", "implement", "refactor"}
VERDICTS = {"behavior_pass", "proxy_green", "still_red", "judge_changed"}
TERMINALS = {
    "end_verified": "verified",
    "end_reported": "reported",
    "end_unverified": "unverified",
    "end_blocked": "blocked",
}
WRITE_STATES = {
    "write",
    "verify_seam",
    "judge_verdict",
    "neighbors",
    "map_terrain",
}


def _bool(value: Any) -> bool:
    return value is True


def _int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value if value > 0 else 0


def _str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _working_set(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    q = _str(raw.get("q")) or "bind"
    return {
        "q": q,
        "mode": _str(raw.get("mode")),
        "working_set": _working_set(raw.get("working_set")),
        "diagnose_attached": _bool(raw.get("diagnose_attached")),
        "evidence_command": _str(raw.get("evidence_command")),
        "evidence_ran": _bool(raw.get("evidence_ran")),
        "wrote": _bool(raw.get("wrote")),
        "shared_touched": _bool(raw.get("shared_touched")),
        "neighbors_ran": _bool(raw.get("neighbors_ran")),
        "seam_ran": _bool(raw.get("seam_ran")),
        "verdict": _str(raw.get("verdict")),
        "rework_count": _int(raw.get("rework_count")),
        "proxy_count": _int(raw.get("proxy_count")),
        "terrain_done": _bool(raw.get("terrain_done")),
    }


def _emit(state: dict[str, Any], q: str, reason: str) -> dict[str, Any]:
    out = dict(state)
    out["q"] = q
    out["terminal"] = q in TERMINALS
    out["kind"] = TERMINALS.get(q, "")
    out["reason"] = reason
    return out


def step(raw: dict[str, Any]) -> dict[str, Any]:
    state = normalize(raw)
    q = state["q"]

    if q not in {
        "bind",
        "select_evidence",
        "run_evidence",
        "gate_write",
        *WRITE_STATES,
        *TERMINALS,
    }:
        return _emit(state, "end_blocked", "unknown state")

    # Named evidence cannot be skipped by jumping to a later state or a terminal.
    if state["diagnose_attached"] and not state["evidence_ran"] and q not in {
        "bind",
        "select_evidence",
        "run_evidence",
    }:
        if state["evidence_command"]:
            return _emit(state, "run_evidence", "diagnose phase 1 has not run")
        return _emit(state, "select_evidence", "diagnose phase 1 has no command yet")

    if state["mode"] == "investigate" and q in WRITE_STATES:
        if state["evidence_ran"]:
            return _emit(state, "end_reported", "investigate does not write product code")
        return _emit(state, "run_evidence", "investigate still owes the red command")

    if q == "end_verified":
        if state["verdict"] != "behavior_pass":
            return _emit(state, "end_unverified", "verified requires behavior_pass")
        if state["shared_touched"] and not state["neighbors_ran"]:
            return _emit(state, "neighbors", "shared state still needs a neighbor run")
        return _emit(state, "end_verified", "terminal")

    if q in TERMINALS:
        return _emit(state, q, "terminal")

    if q == "bind":
        return _emit(state, "select_evidence", "goal and mode are bound")

    if q == "select_evidence":
        if not state["evidence_command"]:
            return _emit(state, "end_blocked", "no evidence command")
        return _emit(state, "run_evidence", "command is bound")

    if q == "run_evidence":
        if not state["evidence_ran"]:
            return _emit(state, "end_blocked", "evidence command has not run")
        return _emit(state, "gate_write", "evidence is in hand")

    if q == "gate_write":
        if state["mode"] not in MODES:
            return _emit(state, "end_blocked", "mode is not one of the four")
        if state["mode"] == "investigate":
            return _emit(state, "end_reported", "investigate stops after evidence")
        if not state["working_set"]:
            return _emit(state, "end_blocked", "no working set")
        return _emit(state, "write", "write is allowed")

    if q == "write":
        if not state["wrote"]:
            return _emit(state, "end_blocked", "working set was not written")
        state["seam_ran"] = False
        return _emit(state, "verify_seam", "same seam must run after the write")

    if q == "verify_seam":
        if not state["seam_ran"]:
            return _emit(state, "end_blocked", "seam has not run since the write")
        return _emit(state, "judge_verdict", "seam output is in hand")

    if q == "judge_verdict":
        verdict = state["verdict"]
        if verdict not in VERDICTS:
            return _emit(state, "end_blocked", "verdict is outside the closed set")
        if verdict == "judge_changed":
            return _emit(state, "end_unverified", "the judge changed")
        if verdict == "proxy_green":
            if state["proxy_count"] < 1:
                state["proxy_count"] = 1
                state["seam_ran"] = False
                return _emit(state, "verify_seam", "proxy green returns to the same seam")
            return _emit(state, "end_unverified", "proxy green repeated")
        if verdict == "still_red":
            if state["rework_count"] >= 3:
                return _emit(state, "end_unverified", "rework limit")
            if state["rework_count"] >= 2 and not state["terrain_done"]:
                return _emit(state, "map_terrain", "two misses require a terrain map")
            state["rework_count"] += 1
            state["wrote"] = False
            state["seam_ran"] = False
            return _emit(state, "write", "still red returns to the working set")
        if state["shared_touched"] and not state["neighbors_ran"]:
            return _emit(state, "neighbors", "behavior passed and shared state was touched")
        return _emit(state, "end_verified", "behavior passed")

    if q == "neighbors":
        if not state["neighbors_ran"]:
            return _emit(state, "end_blocked", "neighbor command has not run")
        if state["verdict"] != "behavior_pass":
            return _emit(state, "end_unverified", "neighbors do not promote a non-pass")
        return _emit(state, "end_verified", "neighbors passed")

    if q == "map_terrain":
        if not state["terrain_done"]:
            return _emit(state, "end_blocked", "terrain map is missing")
        state["wrote"] = False
        state["seam_ran"] = False
        return _emit(state, "write", "third write follows the map")

    return _emit(state, "end_blocked", "no enabled edge")


def _expect(raw: dict[str, Any], q: str) -> None:
    got = step(raw)
    if got["q"] != q:
        raise SystemExit(f"self-check {raw.get('q')} -> {got['q']}, want {q}: {got['reason']}")


def self_check() -> None:
    _expect({"q": "bind", "mode": "debug"}, "select_evidence")
    _expect({"q": "select_evidence", "evidence_command": ""}, "end_blocked")
    _expect(
        {"q": "select_evidence", "evidence_command": "pytest tests/test_cart.py::test_cart_total"},
        "run_evidence",
    )
    _expect(
        {
            "q": "end_verified",
            "diagnose_attached": True,
            "evidence_ran": False,
            "evidence_command": "pytest tests/test_cart.py::test_cart_total",
            "verdict": "behavior_pass",
        },
        "run_evidence",
    )
    _expect(
        {
            "q": "gate_write",
            "mode": "investigate",
            "evidence_ran": True,
            "evidence_command": "pytest tests/test_cart.py::test_cart_total",
        },
        "end_reported",
    )
    _expect(
        {
            "q": "gate_write",
            "mode": "debug",
            "evidence_ran": True,
            "evidence_command": "pytest tests/test_cart.py::test_cart_total",
            "working_set": ["cart.py:total"],
        },
        "write",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "debug",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "proxy_green",
            "proxy_count": 0,
        },
        "verify_seam",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "debug",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "proxy_green",
            "proxy_count": 1,
        },
        "end_unverified",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "debug",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "judge_changed",
        },
        "end_unverified",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "debug",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "still_red",
            "rework_count": 0,
        },
        "write",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "debug",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "still_red",
            "rework_count": 2,
            "terrain_done": False,
        },
        "map_terrain",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "implement",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "behavior_pass",
            "shared_touched": False,
        },
        "end_verified",
    )
    _expect(
        {
            "q": "judge_verdict",
            "mode": "debug",
            "evidence_ran": True,
            "seam_ran": True,
            "verdict": "behavior_pass",
            "shared_touched": True,
            "neighbors_ran": False,
        },
        "neighbors",
    )
    jumped = step(
        {
            "q": "end_verified",
            "mode": "debug",
            "evidence_ran": True,
            "verdict": "proxy_green",
        }
    )
    if jumped["q"] != "end_unverified":
        raise SystemExit(f"self-check jumped verified: {jumped['q']}")
    print("ok: next-state self-check")


def main(argv: list[str]) -> int:
    if "--self-check" in argv:
        self_check()
        return 0
    raw = json.load(sys.stdin)
    if not isinstance(raw, dict):
        raise SystemExit("ledger must be a JSON object")
    json.dump(step(raw), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
