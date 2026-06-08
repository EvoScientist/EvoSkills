---
name: paper-figures
description: "Use this skill to produce standalone, publication-ready PNG graphics and reproducible matplotlib scripts from tabular data (CSVs or DataFrames). This tool is built specifically for rendering numerical data into formal scientific visualizations—including scatter, line, bar, pie, ring, bubble, tornado, KDE, violin, box, heatmap, histogram, and area charts, plus composite multi-panel figures that combine these types in a single image—for scholarly manuscripts. Only trigger this skill when the final deliverable is an individual image file. Do not use this skill for interactive dashboards or HTML-rendered outputs (Plotly, Streamlit, Quarto, Jupyter notebooks), nor when the request involves building a container document or presentation that includes charts (slide deck, conference poster). Finally, it is not for non-data conceptual illustrations like flowcharts, algorithm schematics, or process diagrams. This skill focuses on high-fidelity data rendering into final image files, not presentation design, document layout, or reverse-engineering code from existing screenshots."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '0.1.0'
  tags: [core, figures, visualization, academic-writing]
---

# Paper Figures

A structured approach to producing publication-ready chart figures (PNG) from tabular data plus a natural-language description, using matplotlib.

## When to Use This Skill

- User provides a CSV / dataframe / inline data and asks for a chart
- User describes a target figure in words and wants it rendered
- User mentions "figure", "plot", "chart", "visualize", "render" for a paper or experiment

---

## Inputs and Output

**Inputs the agent will receive:**
- A **data source**: CSV file path, JSON, or inline table.
- A **description**: natural-language text specifying chart type, axes, title, colors, annotations, legend, scenarios, etc. Sometimes terse, sometimes a full paragraph. The description is the full specification — no reference image is provided.

**Output (always):**
- A standalone Python script `plot.py` that:
  - Loads the data from the provided source
  - Renders the figure with `matplotlib`
  - Saves a PNG via `plt.savefig(..., dpi=300, bbox_inches="tight")`
- The rendered `plot.png` next to it (the script is **run** and the PNG produced — do not stop at the script).

**Verification artifacts (write when filesystem access is available):**
- `figure-spec.md` — the compact figure specification extracted before coding.
- `audit.md` — the post-render audit checklist and any repairs made.
- `final-status.md` — one visible status label: `PASSED`, `PASSED_WITH_WARNINGS`, `REPAIRED`, or `FAILED_NEEDS_HANDOFF`.

**Output directory:**
- If the user specifies an output directory (e.g. "save to `path/to/dir/`"), write `plot.py` and `plot.png` inside that directory. Create the directory if it does not exist.
- If no directory is given, write to the current working directory.
- The two filenames are always `plot.py` and `plot.png`. Repeated runs on different inputs go to **different directories**, not different filenames — this keeps the script reference inside the PNG's neighbourhood stable and makes batch comparison easy.

---

## Core Workflow

```
Step 1: Plan Figure        -> verify: description/data ambiguity handled
Step 2: Extract Spec       -> verify: figure-spec.md has all required fields
Step 3: Implement          -> verify: plot.py runs and plot.png exists
Step 4: Audit Figure       -> verify: chart matches spec, data, and description
Step 5: Repair or Finalize -> verify: final-status.md is honest
```

Treat the workflow as a small validation protocol, not a one-shot drawing task. The chart is done only after the audit passes or after you explicitly mark the remaining gap.

### Status Labels

Use exactly one final status:

| Status | Meaning |
|---|---|
| `PASSED` | The figure matches the requested chart type, data fields, scales, labels, series, legend, annotations, and output contract. |
| `PASSED_WITH_WARNINGS` | The figure is usable and faithful to the request, but a minor style/layout mismatch remains and is named in `audit.md`. |
| `REPAIRED` | The first render failed at least one audit item, the script was revised, and the repaired render now passes. |
| `FAILED_NEEDS_HANDOFF` | A required field, chart semantics, package dependency, or visual requirement could not be verified or repaired. Name the exact blocker. |

Do not award `PASSED` because the script ran. Running only proves the PNG exists; it does not prove the figure matches the request.

### Step 1: Plan Figure

Before writing any code, identify from the description:
- **Chart type** (line, bar, scatter, pie, KDE, violin, bubble, tornado, ring, heatmap, …). If ambiguous, prefer the type explicitly named; otherwise infer from the axes/data shape.
- **Axes**: x-label, y-label, units, scale (linear/log), tick formatting. Watch for **shared axes** across subplots, **twin axes** (`ax.twinx()` / `ax.twiny()`) when two series share an x but have different y-units, and **dual / broken axes** when ranges span very different magnitudes.
- **Title**: use the title verbatim if quoted in the description.
- **Series / categories**: how many, names, ordering.
- **Colors**: any specific colors named (use them); otherwise apply the default palette.
- **Annotations**: legend, gridlines, reference lines, data labels.

If the description references quantities ("around 200", "just above 0"), use those as sanity checks against the CSV — descriptions are paraphrased, the CSV is authoritative.

A few patterns that show up repeatedly:
- **Title context for cross-sections**: if the data is a snapshot (a single year, a single experiment), put that context in the title itself — as a parenthetical, comma-separated suffix, or quoted prefix. Don't add a separate "subtitle" via `fig.text` or similar; matplotlib has no clean subtitle API and ad-hoc subtitles tend to drift in alignment and style.
- **Distinguish multi-series, but don't double-encode**: when there is more than one series, the reader must be able to tell them apart — via direct end-of-line labels, a legend, or distinct linestyles paired with a legend. Don't double up (legend AND end-of-line labels for the same series; legend entry AND on-plot text annotation for the same point or region), but don't drop everything either: producing multiple curves with no key is never acceptable.
- **Don't drop data silently**: every series and data point in the input must either appear in the plot or be acknowledged. If a value is off-scale, annotate it at the edge. If a whole series is omitted, the description must justify it. Silent omission is a defect — the reader cannot tell what's missing from the plot alone.
- **Don't invent uninvited elements; do compute what the description asks for**: plot exactly what the description asks for, but no more. Don't add legend entries, annotations, or visual elements the brief didn't request. Don't synthesise extra rows the data doesn't have, and don't compute inferred summaries or aggregations the description doesn't mention. *But*: derived statistics that the description **does** ask for (quartiles, means, smoothed curves, regression fits, density estimates, and similar) are required, not forbidden — compute them faithfully.

If the request has a blocking ambiguity that changes the chart semantics (for example, two possible y variables or an unclear unit conversion), ask one specific question. If the ambiguity is only stylistic, choose the simpler option and record it in `figure-spec.md`.

### Step 2: Inspect the data

Read the first ~10 rows and the column names before writing the plot code. The description gives semantic intent; the CSV gives the structural truth. When they disagree about column names, trust the CSV.

For multi-series data, check whether the data is long-form (one row per (series, x, y)) or wide-form (one column per series). Pivot or melt as needed.

### Step 2.5: Write `figure-spec.md`

Before coding, write a compact Markdown spec. It is the contract the audit will check. Use this shape:

```markdown
# Figure Spec

- chart_type:
- data_sources:
- rows_in_scope:
- data_columns:
- x_axis:
  - field:
  - label:
  - unit:
  - scale:
  - range:
- y_axis:
  - field:
  - label:
  - unit:
  - scale:
  - range:
- additional_axes:
- series_or_categories:
- category_order:
- color_mapping:
- size_mapping:
- legend:
- required_annotations:
- forbidden_elements:
- layout_constraints:
- source_note:
- assumptions:
```

Rules:
- `scale` must be explicit for every numeric axis (`linear`, `log`, `symlog`, etc.).
- `forbidden_elements` must include visual elements that are tempting but not requested, such as regression lines, diagonal reference lines, all-point labels, extra size legends, or aggregation.
- `category_order` must preserve the description order when one is given. Otherwise preserve data order unless sorting is explicitly requested.
- If you derive a statistic, aggregation, fitted line, or smoothed curve, name the calculation under `assumptions`.

### Step 3: Pick the matplotlib idiom

See [references/chart-types.md](references/chart-types.md) for a per-type recipe (one short matplotlib snippet per supported chart type). Read it when you need the right idiom for an unfamiliar type, or to refresh on a tricky one (tornado, ring, KDE).

### Step 4: Apply publication-style defaults

See [references/publication-style.md](references/publication-style.md) for size, fonts, palette, DPI, and savefig conventions. Apply these every time unless the description explicitly contradicts them.

### Step 5: Write the script and run it

- Write the script.
- Execute it with `uv run python plot.py` (this project uses a uv-managed venv — do not invoke `python` directly).
- Confirm the PNG was produced.
- If the script errors, fix and re-run before reporting completion.

When `scripts/validate_figure.py` is available, run it after rendering:

```bash
uv run python <skill-dir>/scripts/validate_figure.py --output-dir <output-dir> --spec <output-dir>/figure-spec.md
```

If `uv` is not available in the environment, use the Python interpreter available to the current workspace, but still run the same validator script.

### Step 6: Audit the result

Re-read the description against your code and the data. Visual inspection of the PNG by the agent is unreliable, so verify structurally instead:
- Did you set the title, both axis labels, and the legend the description asked for?
- Do the series names, ordering, and colors match what the description says?
- Do peak/min/trend locations in the data match the narrative (e.g., if it says "the peak is just above 0", does the data actually peak there)?
- Did you cover every distinct element the description mentions (gridlines, reference lines, annotations)?
- Did any axis ticks disappear that the description didn't ask to remove? If you called `ax.tick_params(length=0)`, `set_xticks([])`, or hid an axis spine, can you justify it against the description? Default state is "ticks visible" — hiding them silently is a defect.
- Histograms in particular: the x-axis ticks are the bin boundaries — never hide them. A histogram without x-ticks is unreadable.
- If you stripped a tick set on purpose (because the description said so), is there a substitute that preserves readability — direct labels at line endpoints, a color bar, or annotation values?
- **Axis bounds must contain everything the description names.** If the brief calls out specific regions, labelled points, or values by name, `ax.set_xlim` / `ax.set_ylim` must include them. Tight framing that crops a named feature off the chart is a defect — equivalent to silent data dropping.

Treat anything missing as a defect and fix the script.

Record the audit in `audit.md`:

```markdown
# Figure Audit

- script_ran: yes/no
- png_exists: yes/no
- chart_type_matches_spec: pass/fail
- data_columns_match_spec: pass/fail
- axis_scales_match_spec: pass/fail
- labels_units_match_spec: pass/fail
- series_category_order_match_spec: pass/fail
- legend_complete_and_uncropped: pass/fail
- annotations_match_spec: pass/fail
- forbidden_elements_absent: pass/fail
- obvious_text_overlap_or_clipping: pass/fail
- repairs_made:
- remaining_warnings:
- final_status:
```

If any required item fails, revise `plot.py`, re-run it, and re-run the audit. Do not mark the task complete while a required item is failed. If a required item cannot be satisfied because the input is contradictory or a dependency is unavailable, set `final_status: FAILED_NEEDS_HANDOFF` and state the exact reason.

---

## Core Design Rules

### 0. Fidelity before styling

Priority order:
1. Match the requested data semantics.
2. Match chart type, axis fields, scale, units, labels, legend, annotations, category order, and visual encodings.
3. Keep the figure readable.
4. Apply publication styling.

Publication styling must not change the chart semantics. Do not add visual elements for polish unless the description asks for them or `figure-spec.md` justifies them.

### 1. The script must be self-contained and reproducible

Hard-code nothing that the user did not ask for. Read data from the provided path; do not synthesize numbers when a CSV exists. The same `plot.py` should regenerate the same PNG on any machine with matplotlib.

### 2. Description is intent, CSV is truth

Descriptions can be paraphrased or rounded. When wording conflicts with the CSV, plot what the CSV says, but match the *narrative* shape (peak locations, trends, orderings) the description implies — a mismatch is a strong signal that you mis-parsed the data.

### 3. One figure, one file, one save

A single `plt.savefig(...)` at the end. Do not litter intermediate `plt.show()` calls (they block in headless environments). No multi-figure scripts unless explicitly asked.

### 4. Prefer matplotlib pyplot for simple cases, OO interface for complex layouts

`plt.plot` / `plt.bar` is fine for a single Axes. The moment you need subplots, twin axes, or per-axes styling, switch to `fig, ax = plt.subplots(...)` and call methods on `ax`. Mixing the two on one figure leads to brittle code.

### 5. Colors carry meaning

If the description names colors ("blue for low, orange for high"), use them — they encode meaning in the reader's eye. Otherwise default to a perceptually-uniform palette (`tab10` is fine for categoricals; `viridis` for sequential).

### 6. Show, don't decorate

Grids, ticks, frames, and annotations should aid reading. Drop chart-junk by default: hide the top/right spines (`ax.spines[['top','right']].set_visible(False)`) for most plots, enable a light y-grid only when comparing magnitudes.

### 7. Leave room for the title

`tight_layout()` will happily crop the title against the top of the axes. Set `"axes.titlepad": 10` in the rcParams block (see `publication-style.md`) or pass `pad=10` to `ax.set_title(...)`. A title that touches the axis is the single most common "looks unfinished" tell in a generated figure.

### 8. Multi-panel layouts use gridspec, not stacked savefigs

The deliverable is a single PNG. When the description calls for multiple sub-plots (a main chart with side panels, a 2×2 comparison grid, a chart plus an inset), compose them in one figure via `fig.add_gridspec(...)` and a single `savefig`. Don't emit multiple PNGs; the eval harness consumes one. See `chart-types.md` → multi-panel composition.

### 9. Reach for matplotlib's high-level API; avoid hand-rolled coordinate math

When matplotlib already ships a helper for a layout, annotation, or formatting task — `inset_axes` for sub-axes anchored to data, `gridspec` for panel composition, `bar_label` for per-bar value annotations, `tight_layout` / `constrained_layout` for margin resolution, `ticker.FuncFormatter` for axis label formatting — use it instead of computing positions, transforms, or text placements by hand. The high-level helpers survive figure resizes, DPI changes, and downstream `subplots_adjust` calls; manual coordinate transforms break the moment the layout shifts. If you find yourself writing pixel arithmetic or chaining `ax.transData` / `ax.transAxes` manually, stop and look for the built-in first.

---

## Counterintuitive Notes

### Don't trust the chart-type label alone

A "tornado chart" in the description may technically be a horizontal grouped bar chart (positive/negative bars per category). Read the **shape** the description implies before picking the recipe — and verify against the data layout.

### Numbers in prose are approximate

Descriptions say "around 200" when the value is 187.4. Plot 187.4. Only deviate from the CSV if it is clearly wrong (e.g. unit mismatch the description corrects).

### Style defaults beat ad-hoc styling

Every time you tweak `rcParams` for one plot, you create a one-off look that's hard to compare across figures. Apply the publication defaults from `publication-style.md` consistently — only override per-figure when the description demands it.

---

## Reference Navigation

| Topic | Reference File | When to Use |
|-------|---------------|-------------|
| Chart-type recipes | [chart-types.md](references/chart-types.md) | Need the right matplotlib idiom for a specific chart type |
| Publication style | [publication-style.md](references/publication-style.md) | Setting figure size, fonts, palette, DPI, savefig |
