---
name: iterative-coder
description: "Iterative code refinement through plan → code → evaluate → refine cycles. Runs lint checks (ruff), tests (pytest), and structured self-evaluation each cycle, then diagnoses failures and refines. Decomposes complex tasks into sequential phases, iterates up to 3 times per phase (10 total). Use when: the main agent delegates a code task with 'MODE: MORE_EFFORT', the user selects 'More Effort' code generation mode, or the task explicitly requests iterative refinement for higher code quality. Do NOT use for single-pass code generation (Lite mode), experiment pipeline orchestration (use experiment-pipeline), or diagnosing a specific experiment failure (use experiment-craft)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, code-generation, iteration, refinement]
---

# Iterative Coder

Iterative code refinement through structured plan → code → evaluate → refine cycles. Each cycle runs objective checks (lint, tests) and self-evaluation, then diagnoses failures and plans targeted improvements. Reaches production quality in 3-8 iterations.

## When to Use This Skill

- Main agent delegates a code task prefixed with "MODE: MORE_EFFORT"
- User selected "More Effort" mode for code generation
- Task requires high code quality with verified correctness
- Task involves complex implementation (5+ files, multiple modules)
- You want to iterate on code quality rather than submit first-pass code
- You mention "iterative refinement", "code quality loop", "plan-code-evaluate"

## The Iteration Mindset

**Code quality comes from fast feedback loops, not careful first attempts.** A fast plan → code → evaluate → fix cycle beats spending 30 minutes on a "perfect" first implementation. The evaluate step reveals problems you cannot predict by thinking alone — lint errors, import failures, test regressions, and missing edge cases all surface immediately when you actually run the code.

## Before Starting: Load Context

1. Read `/memory/experiment-memory.md` for proven strategies from past cycles (skip if it doesn't exist)
2. Identify existing tests, linting config (pyproject.toml, ruff.toml), or CI setup in the workspace
3. Check available tools:
   ```bash
   ruff --version 2>&1; echo "---"; python -m pytest --version 2>&1
   ```
   If either is missing, you will skip that check during evaluation (do not fail the iteration).

## Phase Decomposition

Before iterating, analyze the task and break it into sequential phases:

| Task Complexity | Recommended Phases |
|-----------------|-------------------|
| Single file, well-defined function | 1 phase |
| 2-4 files, clear interfaces | 2 phases |
| 5+ files, multiple interacting modules | 3-5 phases |

For each phase, define:
- **Name**: concise label (e.g., "Data loading pipeline")
- **Goal**: what "done" looks like for this phase
- **Verification signal**: how to confirm the phase is complete (specific test, lint clean, output matches)

Order phases by dependency — later phases may build on earlier ones.

## The Iteration Loop

For each phase, iterate up to **3 times**. Global maximum: **10 iterations** across all phases.

### Step 1: Plan

Read current code and previous evaluation feedback (if any). Write a concise improvement plan.

**First iteration of a phase**: Write an initial implementation plan based on the phase goal.

**Subsequent iterations**: Analyze the last evaluation's feedback and diagnose the root cause of failures before planning changes. Do not repeat the same approach that already failed.

Adapt your plan based on the failure mode from the last evaluation:

| Last Failure | Planned Response |
|-------------|-----------------|
| Timeout | Add `--quick`/`--smoke` mode, reduce data size, add early stopping |
| Syntax Error | Simplify logic, run `python -c "import ast; ast.parse(open('file.py').read())"` to validate before running |
| Import Error | Check `pip list`, use only installed packages, add missing deps to requirements |
| Test Failure | Focus on the specific failing test, make minimal targeted changes |
| Lint Failure | Run `ruff check --fix . && ruff format .` before any logic changes |
| Low self-assessment | Re-read the original task requirements, check for missing functionality |

### Step 2: Code

Implement the plan. Keep changes focused on what the plan specifies.

- Do not rewrite working files unless the plan explicitly requires it
- After writing code, do a quick sanity read of the changed files

### Step 3: Evaluate

**CRITICAL: You MUST run these commands every iteration. Do not skip evaluation.**

```bash
# 1. Lint check
ruff check . 2>&1 | tail -20
echo "LINT_EXIT: $?"

# 2. Format check
ruff format --check . 2>&1 | tail -10
echo "FORMAT_EXIT: $?"

# 3. Run tests (only if test files exist in workspace)
python -m pytest -x -q --tb=short 2>&1 | tail -30
echo "TEST_EXIT: $?"
```

If `ruff` is not installed, skip checks 1-2. If `pytest` is not installed or no test files exist, skip check 3. Record which checks were skipped.

### Step 4: Score

Compute a composite score from objective signals and self-assessment.

**Objective signals** (from Step 3 exit codes):
- `LINT_EXIT=0` → lint_score = 1.0, else lint_score = 0.0
- `FORMAT_EXIT=0` → format_score = 1.0, else format_score = 0.0
- `TEST_EXIT=0` → test_score = 1.0, else parse pass ratio from pytest output (e.g., "3 passed, 1 failed" → 0.75)

**Self-assessment** (rate 0.0 – 1.0):
Evaluate on: correctness (does the code do what was asked?), completeness (all requirements addressed?), error handling (reasonable edge cases covered?), readability (clear names, structure).

**Composite score** — dynamic weighting based on available signals:
- Lint + tests available: `0.2 × lint + 0.1 × format + 0.3 × test + 0.4 × self`
- Lint only (no tests): `0.3 × lint + 0.1 × format + 0.6 × self`
- Tests only (no ruff): `0.4 × test + 0.6 × self`
- Neither available: `1.0 × self`

**Self-assessment hard caps** — prevent score inflation from self-assessment:
- If lint check FAILED → composite capped at **0.4**, regardless of self-assessment
- If any test FAILED → composite capped at **0.6**
- Only claim composite ≥ 0.85 if BOTH lint and tests pass AND implementation is complete
- Deductions: missing error handling for obvious cases (−0.1), hardcoded absolute paths (−0.05)

See [references/evaluation-protocol.md](references/evaluation-protocol.md) for detailed scoring edge cases.

### Step 5: Decide

- Composite score **≥ 0.85** → advance to next phase (or finish if last phase)
- Composite score **< 0.85** → return to Step 1 with evaluation feedback
- **Phase iteration limit reached** (3 per phase) → advance to next phase anyway, note remaining issues
- **Global iteration limit reached** (10 total) → stop, output current best result

### Step 6: Log

**CRITICAL: Append to `/artifacts/iteration_log.md` after every iteration.**

Use the template at [assets/iteration-log-template.md](assets/iteration-log-template.md):

```markdown
## Iteration {N} (Phase {M}/{T})
- **Score**: {composite} (lint={X} format={X} test={X} self={X})
- **Lint**: passed/failed ({N} issues)
- **Tests**: passed/failed ({passed}/{total})
- **Changes**: [{files changed}]
- **Feedback**: [{key evaluation findings}]
- **Next**: continue / next_phase / done
```

## Completion

After all phases complete or global iteration limit is reached:

1. **Report** to the caller:
   - Total iterations used
   - Final composite score
   - Key improvements per phase (1-2 sentences each)
2. **List** all output file paths (code, configs, tests)
3. **Note** remaining issues: lint warnings, missing tests, known limitations, TODOs

## Counterintuitive Iteration Rules

1. **Fix lint before logic**: Lint errors compound — one import error masks all test failures downstream. Always run `ruff check --fix .` before investigating logic bugs.

2. **3 iterations is enough per phase**: If you cannot fix it in 3 targeted iterations, the problem is architectural (wrong decomposition), not incremental. Advance to the next phase or re-plan rather than iterating further.

3. **Tests reveal more than reading**: Running tests for 10 seconds teaches you more about correctness than reading code for 5 minutes. Always run tests, even when you are confident the code is correct.

4. **Score drops are information**: If your composite score drops after a change, that is a signal about what matters. Analyze why it dropped before undoing the change.

5. **Don't gold-plate**: 0.85 is the target, not 1.0. Diminishing returns kick in hard above 0.9. Ship and iterate in the next conversation if needed.

## Skill Integration

### Before Starting (load memory)
Refer to **evo-memory** → Read `/memory/experiment-memory.md` for prior strategies

### On Failure (stuck after max iterations)
Refer to **experiment-craft** → 5-step diagnostic flow to understand the root cause before retrying

### On Success (all phases complete, score ≥ 0.85)
Report to the main agent → main agent continues pipeline (data-analysis, writing, etc.)

### Handoff Artifacts

| Artifact | Location | Used By |
|----------|----------|---------|
| Iteration log | `/artifacts/iteration_log.md` | Main agent summary, evo-memory ESE |
| Final code | Workspace root | Next pipeline step |
| Test results | Iteration log entries | data-analysis-agent |

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Scoring rules and edge cases | [evaluation-protocol.md](references/evaluation-protocol.md) | When scoring edge cases arise (partial tests, missing tools) |
| Iteration log template | [iteration-log-template.md](assets/iteration-log-template.md) | Every iteration (Step 6) |
