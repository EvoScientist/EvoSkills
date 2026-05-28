#!/usr/bin/env python3
"""Saturation-based stopping for iterative paper collection.

Tracks how many new relevant papers each search round contributes,
fits a coverage model over the per-round yields, and reports whether
the round-over-round rate has dropped far enough that continuing is
unlikely to find much more of the relevant literature.

This lets open-ended surveys stop on a principled signal ("~90%
coverage reached") instead of an arbitrary round cap, and lets
narrow queries keep going when round 4 is still productive.

State model: a JSONL log, one line per round, produced by:

    saturation.py record --log /tmp/sat.jsonl --round 1 \\
        --candidates 50 --new-relevant 18 --new-ids id1,id2,...

Once at least --min-rounds rounds (default 3) are logged, ask:

    saturation.py estimate --log /tmp/sat.jsonl

Produces a JSON estimate with `coverage_estimate` in [0, 1],
`should_stop` (bool), a reason string, and the `method` used
(`chao1` when --new-ids were supplied, otherwise `heuristic`).

Designed to be called inside the Thorough Mode loop. The script is
also importable: `from saturation import fit, Round`.

Commands:
    record              Append one round to the log
    estimate            Fit and report coverage
    reset               Delete the log
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any


DEFAULT_MIN_ROUNDS = 3
DEFAULT_STOP_RATE = 0.05  # new-relevant / candidates below this → slow
DEFAULT_DROPOFF = 0.75  # round-over-round drop ≥ 75% → saturating
DEFAULT_COVERAGE_TARGET = 0.90  # Chao1-estimated coverage to trigger stop


@dataclass
class Round:
    round: int
    query: str = ""
    candidates: int = 0
    new_relevant: int = 0
    new_ids: list[str] = field(default_factory=list)
    timestamp: str = ""


def _load_log(path: str) -> list[Round]:
    if not os.path.exists(path):
        return []
    rounds: list[Round] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            rounds.append(
                Round(
                    round=int(d["round"]),
                    query=d.get("query", ""),
                    candidates=int(d.get("candidates", 0)),
                    new_relevant=int(d.get("new_relevant", 0)),
                    new_ids=list(d.get("new_ids") or []),
                    timestamp=d.get("timestamp", ""),
                )
            )
    rounds.sort(key=lambda r: r.round)
    return rounds


def _append_round(path: str, rec: Round) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(
            json.dumps(
                {
                    "round": rec.round,
                    "query": rec.query,
                    "candidates": rec.candidates,
                    "new_relevant": rec.new_relevant,
                    "new_ids": rec.new_ids,
                    "timestamp": rec.timestamp,
                }
            )
            + "\n"
        )


def record_round(
    log_path: str,
    *,
    query: str = "",
    candidates: int = 0,
    new_relevant: int = 0,
    new_ids: list[str] | None = None,
    timestamp: str = "",
    round: int | None = None,
) -> int:
    """Public helper: append a round to the log, auto-numbering when `round` is None.

    Returns the round number actually written. Other scripts (e.g.
    batch_collect, score_papers) call this to keep the saturation
    log as a side effect of their main work, so the model doesn't
    have to invoke `saturation.py record` by hand.
    """
    if round is None:
        existing = _load_log(log_path)
        round = (existing[-1].round + 1) if existing else 1
    _append_round(
        log_path,
        Round(
            round=round,
            query=query,
            candidates=candidates,
            new_relevant=new_relevant,
            new_ids=list(new_ids or []),
            timestamp=timestamp,
        ),
    )
    return round


# ── Coverage estimators ──────────────────────────────────────────


def _chao1(rounds: list[Round]) -> tuple[float | None, int, int, int]:
    """Chao1 richness estimator using per-round paper IDs.

    Treat each round as a "sample." A paper observed in k rounds is
    a k-ton. Chao1: N ≈ S_obs + f1² / (2 * (f2 + 1)), where f1/f2
    are singletons/doubletons. Returns (estimate, S_obs, f1, f2) or
    (None, ...) when IDs aren't available.
    """
    if not all(r.new_ids for r in rounds if r.new_relevant > 0):
        return None, 0, 0, 0
    seen: dict[str, int] = {}
    for r in rounds:
        for pid in r.new_ids:
            seen[pid] = seen.get(pid, 0) + 1
    s_obs = len(seen)
    if s_obs == 0:
        return None, 0, 0, 0
    f1 = sum(1 for c in seen.values() if c == 1)
    f2 = sum(1 for c in seen.values() if c == 2)
    # Bias-corrected Chao1 (handles f2 == 0 without singularity)
    est = s_obs + (f1 * f1) / (2 * (f2 + 1))
    return est, s_obs, f1, f2


def _rates(rounds: list[Round]) -> list[float]:
    """Yield rate per round (new_relevant / candidates)."""
    out: list[float] = []
    for r in rounds:
        if r.candidates <= 0:
            out.append(0.0)
        else:
            out.append(r.new_relevant / r.candidates)
    return out


def fit(
    rounds: list[Round],
    min_rounds: int = DEFAULT_MIN_ROUNDS,
    stop_rate: float = DEFAULT_STOP_RATE,
    dropoff: float = DEFAULT_DROPOFF,
    coverage_target: float = DEFAULT_COVERAGE_TARGET,
) -> dict[str, Any]:
    """Fit a stopping decision over the logged rounds.

    Returns a dict with coverage_estimate, should_stop, reason,
    method, and the raw rates. Callers can persist this next to the
    log.
    """
    # Narrow-rubric short-circuit: when ≥2 consecutive rounds yielded zero
    # new relevant papers, more rounds won't help — the rubric is too
    # restrictive (or the pool is exhausted under the rubric's threshold).
    # Fires BEFORE the min_rounds gate because the standard "insufficient
    # → CONTINUE" verdict otherwise produces wasted iterations on
    # narrow-rubric queries where passes_all=0/N every round.
    if len(rounds) >= 2:
        recent = rounds[-2:]
        if all(r.new_relevant == 0 for r in recent):
            return {
                "method": "narrow-rubric",
                "rounds": len(rounds),
                "should_stop": True,
                "reason": (
                    f"{len(recent)} consecutive rounds returned 0 new "
                    "relevant papers — rubric is likely too narrow or "
                    "the relevant pool is exhausted at this threshold. "
                    "Consider re-authoring the rubric with broader "
                    "criteria, or relaxing the disqualifiers."
                ),
                "coverage_estimate": None,
                "rates": _rates(rounds),
            }

    if len(rounds) < min_rounds:
        return {
            "method": "insufficient",
            "rounds": len(rounds),
            "min_rounds": min_rounds,
            "should_stop": False,
            "reason": (
                f"Only {len(rounds)} round(s) logged; need ≥{min_rounds} "
                "for a stable estimate"
            ),
            "coverage_estimate": None,
            "rates": _rates(rounds),
        }

    rates = _rates(rounds)
    total_relevant = sum(r.new_relevant for r in rounds)

    # Prefer Chao1 when IDs are present — it's a proper richness estimator.
    chao_est, s_obs, f1, f2 = _chao1(rounds)
    coverage: float | None = None
    method = "heuristic"
    if chao_est is not None and chao_est > 0:
        coverage = s_obs / chao_est
        method = "chao1"

    # Heuristic stops — also computable without IDs.
    last = rates[-1]
    prev = rates[-2]
    last_two_low = last <= stop_rate and prev <= stop_rate
    big_dropoff = prev > 0 and (prev - last) / prev >= dropoff
    # New-per-round absolute counts trending toward zero is another signal,
    # independent of candidates (because candidates may drop too).
    abs_last = rounds[-1].new_relevant
    abs_prev = rounds[-2].new_relevant
    abs_big_dropoff = abs_prev > 0 and (abs_prev - abs_last) / abs_prev >= dropoff

    reasons: list[str] = []
    should_stop = False
    if coverage is not None and coverage >= coverage_target:
        should_stop = True
        reasons.append(
            f"coverage_estimate={coverage:.2f} ≥ target {coverage_target:.2f} "
            f"(Chao1: observed {s_obs}, estimated {chao_est:.1f}; "
            f"f1={f1}, f2={f2})"
        )
    if last_two_low:
        should_stop = True
        reasons.append(
            f"last 2 rounds yield-rate ≤ {stop_rate:.2f} ({prev:.2f} → {last:.2f})"
        )
    if big_dropoff or abs_big_dropoff:
        should_stop = True
        reasons.append(
            f"round-over-round drop ≥ {dropoff:.0%} "
            f"(prev rate {prev:.2f} → {last:.2f}; "
            f"prev abs {abs_prev} → {abs_last})"
        )

    if not should_stop:
        reasons.append(
            "continue — last-round rate {:.2f} above threshold {:.2f}".format(
                last,
                stop_rate,
            )
        )

    return {
        "method": method,
        "rounds": len(rounds),
        "should_stop": should_stop,
        "coverage_estimate": coverage,
        "total_relevant": total_relevant,
        "rates": rates,
        "chao1": (
            None
            if chao_est is None
            else {
                "observed": s_obs,
                "estimated": round(chao_est, 2),
                "singletons": f1,
                "doubletons": f2,
            }
        ),
        "reason": "; ".join(reasons),
        "thresholds": {
            "stop_rate": stop_rate,
            "dropoff": dropoff,
            "coverage_target": coverage_target,
        },
    }


# ── CLI ──────────────────────────────────────────────────────────


def _cmd_record(args: argparse.Namespace) -> None:
    ids: list[str] = []
    if args.new_ids:
        ids = [pid.strip() for pid in args.new_ids.split(",") if pid.strip()]
    rec = Round(
        round=args.round,
        query=args.query or "",
        candidates=args.candidates,
        new_relevant=args.new_relevant,
        new_ids=ids,
        timestamp=args.timestamp or "",
    )
    _append_round(args.log, rec)
    print(
        json.dumps(
            {
                "status": "ok",
                "log": args.log,
                "round": rec.round,
                "new_relevant": rec.new_relevant,
            }
        )
    )


def _cmd_estimate(args: argparse.Namespace) -> None:
    rounds = _load_log(args.log)
    result = fit(
        rounds,
        min_rounds=args.min_rounds,
        stop_rate=args.stop_rate,
        dropoff=args.dropoff,
        coverage_target=args.coverage_target,
    )
    if args.json:
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["should_stop"] or args.exit_zero else 2)
    print(f"rounds: {result['rounds']}")
    print(f"method: {result['method']}")
    cov = result.get("coverage_estimate")
    print("coverage_estimate: " + ("n/a" if cov is None else f"{cov:.2f}"))
    rates_fmt = ", ".join(f"{r:.2f}" for r in result.get("rates") or [])
    print(f"rates: [{rates_fmt}]")
    if result.get("chao1"):
        c = result["chao1"]
        print(
            f"chao1: observed={c['observed']} "
            f"estimated={c['estimated']} "
            f"singletons={c['singletons']} doubletons={c['doubletons']}"
        )
    decision = "STOP" if result["should_stop"] else "CONTINUE"
    print(f"decision: {decision}")
    print(f"reason: {result['reason']}")
    sys.exit(0 if result["should_stop"] or args.exit_zero else 2)


def _cmd_reset(args: argparse.Namespace) -> None:
    if os.path.exists(args.log):
        os.remove(args.log)
    print(json.dumps({"status": "ok", "removed": args.log}))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Saturation-based stopping for iterative paper collection.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="Append one round to the log")
    rec.add_argument("--log", required=True, help="Path to the JSONL saturation log")
    rec.add_argument(
        "--round", type=int, required=True, help="Round number (1-indexed)"
    )
    rec.add_argument(
        "--query", default="", help="Query used this round (informational)"
    )
    rec.add_argument(
        "--candidates", type=int, required=True, help="Papers screened this round"
    )
    rec.add_argument(
        "--new-relevant",
        type=int,
        required=True,
        help="Relevant papers unseen before this round",
    )
    rec.add_argument(
        "--new-ids",
        default="",
        help="Comma-separated IDs of new relevant papers (enables Chao1)",
    )
    rec.add_argument("--timestamp", default="", help="Optional ISO timestamp")
    rec.set_defaults(func=_cmd_record)

    est = sub.add_parser("estimate", help="Fit and report coverage")
    est.add_argument("--log", required=True)
    est.add_argument("--min-rounds", type=int, default=DEFAULT_MIN_ROUNDS)
    est.add_argument(
        "--stop-rate",
        type=float,
        default=DEFAULT_STOP_RATE,
        help="Yield-rate threshold: last 2 rounds below this → stop",
    )
    est.add_argument(
        "--dropoff",
        type=float,
        default=DEFAULT_DROPOFF,
        help="Round-over-round drop fraction to treat as saturating",
    )
    est.add_argument(
        "--coverage-target",
        type=float,
        default=DEFAULT_COVERAGE_TARGET,
        help="Chao1 coverage ≥ this → stop",
    )
    est.add_argument("--json", action="store_true")
    est.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0 (default: exit 2 when decision=CONTINUE, useful in shell loops)",
    )
    est.set_defaults(func=_cmd_estimate)

    rst = sub.add_parser("reset", help="Delete the saturation log")
    rst.add_argument("--log", required=True)
    rst.set_defaults(func=_cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
