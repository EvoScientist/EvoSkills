"""JSONL sidecar logger + running token/cost totals + scratchpads sidecar."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Logger:
    """JSONL sidecar logger + stderr progress + running totals.

    One JSON record per pipeline event. Use ``.event(stage, **fields)`` to
    log a lightweight breadcrumb, or ``.llm(stage, prompt, response, ...)``
    to capture full LLM I/O — the LLM helper also accumulates token and
    cost totals which are emitted as a ``summary`` event by ``.finalize()``.
    With ``verbose=True``, prompts and responses are also mirrored to stderr.
    """

    def __init__(self, path: Path | None, verbose: bool = False):
        self.path = path
        self.verbose = verbose
        self._fp = None
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fp = path.open("w", encoding="utf-8")
        # Running totals across the full pipeline.
        self.totals: dict[str, Any] = {
            "llm_calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
            "duration_s": 0.0,
        }
        # Last LLM context — used to write a focused stderr diagnostic if
        # the pipeline aborts. Updated on every llm() call.
        self.last_stage: str | None = None
        self.last_prompt: str | None = None
        self.last_response: str | None = None
        # Per-section scratchpads keyed by "C<challenge>_S<solution>".
        # Captured from detail_to_mermaid's `detail_scratchpad` events and
        # written to a sidecar JSON at close — invaluable for diagnosing
        # which edges/EPs were dropped versus emitted and why.
        self.scratchpads: dict[str, dict[str, Any]] = {}

    def _write(self, record: dict[str, Any]) -> None:
        record.setdefault("ts", datetime.now(timezone.utc).isoformat())
        if self._fp is not None:
            self._fp.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._fp.flush()

    def event(self, stage: str, **fields: Any) -> None:
        # Intercept detail_scratchpad events so the developer-facing
        # sidecar file can be written cleanly at close time. The JSONL log
        # still receives the event verbatim — both views are useful.
        if stage == "detail_scratchpad":
            c_idx = fields.get("challenge_idx")
            sol_key = fields.get("solution_key", "")
            key = f"C{c_idx}_S{sol_key}"
            self.scratchpads[key] = {
                "challenge_idx": c_idx,
                "solution_key": sol_key,
                "scratchpad": fields.get("scratchpad", ""),
                "truncated": fields.get("truncated", False),
            }
        self._write({"stage": stage, **fields})

    def llm(
        self,
        stage: str,
        prompt: str,
        response: str,
        *,
        duration_s: float,
        usage: dict[str, Any] | None = None,
        **fields: Any,
    ) -> None:
        usage = usage or {}
        self.last_stage = stage
        self.last_prompt = prompt
        self.last_response = response
        # Accumulate. Missing fields stay at their previous total.
        self.totals["llm_calls"] += 1
        self.totals["duration_s"] = round(self.totals["duration_s"] + duration_s, 3)
        for k in (
            "prompt_tokens",
            "completion_tokens",
            "cached_tokens",
            "reasoning_tokens",
            "total_tokens",
        ):
            v = usage.get(k)
            if isinstance(v, (int, float)):
                self.totals[k] += int(v)
        cost = usage.get("cost")
        if isinstance(cost, (int, float)):
            self.totals["cost"] = round(self.totals["cost"] + float(cost), 6)
        self._write(
            {
                "stage": stage,
                "kind": "llm",
                "prompt": prompt,
                "response": response,
                "duration_s": round(duration_s, 3),
                "usage": usage,
                **fields,
            }
        )
        if self.verbose:
            # Verbose mirror goes to stdout — stderr is reserved for the
            # focused failure diagnostic emitted by _generate_async.
            print(
                f"\n--- LLM [{stage}] ({duration_s:.1f}s) ---\n"
                f">>> PROMPT (first 600 chars):\n{prompt[:600]}\n"
                f"<<< RESPONSE (first 600 chars):\n{response[:600]}\n"
            )

    def finalize(self) -> dict[str, Any]:
        """Emit a 'summary' event with cumulative totals and return them."""
        self._write({"stage": "summary", **self.totals})
        return dict(self.totals)

    def write_scratchpads(self, path: Path) -> None:
        """Write the collected scratchpads to a sidecar JSON file.

        Sections preserved in canonical order (sorted by key). Skipped
        entirely when no scratchpads were collected — keeps the success
        case from leaving an empty file on disk.
        """
        if not self.scratchpads:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered = {k: self.scratchpads[k] for k in sorted(self.scratchpads)}
        path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2))

    def close(self) -> None:
        if self._fp is not None:
            self._fp.close()
            self._fp = None
