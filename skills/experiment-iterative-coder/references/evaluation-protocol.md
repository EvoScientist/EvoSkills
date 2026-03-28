# Evaluation Protocol — Scoring Rules and Edge Cases

This reference documents the full scoring logic for the iterative-coder skill's
evaluate → score cycle. Refer to this when edge cases arise during scoring.

## Objective Signal Collection

### Lint (ruff check)

| Exit Code | lint_score | lint_passed |
|-----------|-----------|-------------|
| 0 | 1.0 | true |
| non-zero | 0.0 | false |
| ruff not installed | skip (exclude from weighting) | N/A |

### Format (ruff format --check)

| Exit Code | format_score | Notes |
|-----------|-------------|-------|
| 0 | 1.0 | All files formatted |
| non-zero | 0.0 | Files need formatting |
| ruff not installed | skip | Exclude from weighting |

### Tests (pytest)

| Exit Code | test_score | tests_passed |
|-----------|-----------|--------------|
| 0 | 1.0 | true |
| non-zero | parse pass ratio | false |
| no test files found | skip (exclude from weighting) | N/A |
| pytest not installed | skip | N/A |
| timeout (>300s) | 0.0 | false |

**Pass ratio parsing**: Look for pytest summary line like `5 passed, 2 failed`.
Compute `passed / (passed + failed)`. If no summary found, score = 0.0.

## Composite Score Weighting

The composite formula adapts to which signals are available:

| Available Signals | Formula |
|-------------------|---------|
| lint + format + test | `0.2×lint + 0.1×format + 0.3×test + 0.4×self` |
| lint + format (no test) | `0.3×lint + 0.1×format + 0.6×self` |
| test only (no ruff) | `0.4×test + 0.6×self` |
| none | `1.0×self` |

## Self-Assessment Hard Caps

These caps override the composite formula to prevent inflated scores when
objective signals indicate problems:

| Condition | Cap | Rationale |
|-----------|-----|-----------|
| lint check failed (exit ≠ 0) | 0.4 | Lint errors block test reliability |
| any test failed | 0.6 | Failing tests = incomplete correctness |
| lint failed AND test failed | 0.3 | Both signals negative = serious issues |

**Cap application**: After computing the weighted composite, apply
`composite = min(composite, cap)`.

Only claim composite ≥ 0.85 when ALL of:
- lint check passed (or ruff unavailable)
- all tests passed (or no tests exist)
- implementation covers all stated requirements

## Self-Assessment Deductions

Apply these deductions to the self-assessment score (before weighting):

| Issue | Deduction | When to Apply |
|-------|-----------|---------------|
| Missing error handling for obvious failure cases | −0.1 | File I/O without try/except, network calls without timeout |
| Hardcoded absolute paths | −0.05 | `/home/user/...` instead of relative or configurable paths |
| No docstrings on public module/class/function | −0.05 | Only for public APIs, not internal helpers |
| Incomplete implementation (TODO/FIXME left in code) | −0.15 | Core functionality not implemented |

## Edge Cases

### No objective signals available (neither ruff nor pytest)

Score = 1.0 × self-assessment. In this case, be extra conservative with
self-assessment. Without objective checks, cap self-assessment at 0.7 unless
you have strong evidence of correctness (e.g., manually verified output).

### Tests exist but all are skipped

If pytest reports "0 passed, 0 failed, N skipped", treat as test_score = 0.5
(tests exist but provide no signal). Note in the iteration log.

### Partial lint pass

If `ruff check` passes but `ruff format --check` fails, this counts as
lint partially passed. lint_score = 0.5 (check OK, format not OK).
The hard cap (0.4) does NOT apply for format-only failures — only
for `ruff check` failures.

### Test timeout

If pytest times out (>300 seconds), test_score = 0.0 and failure_mode = "timeout".
The iteration plan should add `--timeout=60` per test or reduce test data.
