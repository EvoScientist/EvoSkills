# Publication Style

Defaults for matplotlib figures destined for scientific papers. Apply these unless the description explicitly contradicts them.

---

## Priority

Publication style is the final pass, not the source of chart semantics. Apply this priority order:

1. Match the requested data fields, transformations, filters, and aggregation level.
2. Match chart type, axis scale, units, category order, legend, and annotations.
3. Preserve readability: no clipped legends, no unreadable labels, no avoidable text overlap.
4. Apply the style defaults in this file.

Do not add visual elements for style alone. A clean but semantically wrong figure is a failed figure.

## Sizing

| Use | `figsize` (inches) | Notes |
|-----|--------------------|-------|
| Single-column figure | `(3.5, 2.6)` | Standard 1-column width in most LaTeX templates |
| 1.5-column figure | `(5.0, 3.5)` | Useful for slightly wider visualizations |
| Double-column (full width) | `(7.0, 4.5)` | Spans both columns; reserve for figures that justify the space |
| Square figure (heatmap, scatter) | `(4.0, 4.0)` | Aspect 1:1 when both axes carry equal weight |

Default to single-column unless the description implies otherwise (many series, multi-panel, long x-axis ranges).

For multi-panel figures, scale the height by the number of rows: `figsize=(7, 2.5 * nrows)`.

**Default scale: linear.** Set `ax.set_xscale("log")` / `set_yscale("log")` when the description, metadata, reference text, or `figure-spec.md` requires it. Wide data ranges are not on their own sufficient justification — try a humanised tick formatter (see *Tick formatters* below) first; reach for log when the task semantics call for it. For chart-name-only datasets, record the scale decision in `figure-spec.md` before coding.

---

## DPI and saving

```python
plt.savefig("plot.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
```

- **300 dpi** is the minimum for print-quality raster output.
- **`bbox_inches="tight"`** crops whitespace around the axes (otherwise you ship a postage-stamp plot inside a poster).
- Avoid `transparent=True` unless the description asks for it — opaque white is safer for figure embedding.

If the description asks for a vector format, also write `plot.pdf` (or `.svg`) alongside the PNG.

---

## Fonts and text sizes

Sans-serif is the safe default. Set sizes globally before plotting:

```python
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titlepad": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
})
```

10-11pt body text reads cleanly at single-column width. Drop to 8-9pt for dense multi-panel figures, never below 7pt.

Use LaTeX rendering (`"text.usetex": True`) only when the paper uses LaTeX-rendered text consistently — it slows rendering and brittles on machines without a TeX install.

---

## Colors and palettes

**Categorical (≤10 categories):** matplotlib's `tab10` (default cycle). Distinct hues, perceptually well-spaced.

**Sequential (ordered magnitude):** `viridis`. Perceptually uniform, colorblind-safe, prints sensibly in greyscale.

**Diverging (signed deviations):** `RdBu_r` or `coolwarm`. Centered at zero by passing `vmin=-vmax, vmax=vmax` to imshow/pcolormesh.

**Colorblind-safe categorical:** Okabe-Ito palette
```python
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
             "#0072B2", "#D55E00", "#CC79A7", "#000000"]
```

When the description names specific colors ("blue and orange bars"), use them verbatim. Match on name (`"tab:blue"`, `"tab:orange"`) for matplotlib-native colors.

---

## Spines, ticks, grid

Strip chart-junk by default:

```python
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(direction="out", length=4)
```

- Keep left and bottom spines.
- **Gridlines**: enable a light y-grid (`ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.7)`) when readers compare magnitudes; disable the grid for scatter/density plots where it clutters.
- Tick direction `"out"` keeps the data area clean.

For polar plots (ring, pie radials), keep the polar frame on.

---

## Titles and labels

- **Title**: at most one line. If the description quotes a title in quotes, use it verbatim. Always leave breathing room above the axes — the rcParams block above sets `axes.titlepad: 10`, or pass `pad=10` to `set_title`. A title kissing the axis is the single most common "looks unfinished" tell.
- **Axis labels**: include units in parentheses (`"Imports (billion 2005 US$)"`).
- **Legend**: see the *Legend placement* section below.

---

## Legend placement

Pick legend placement based on the *layout*, not just per-plot eyeballing.

**Single-axes, single-chart-type plots → `ax.legend(loc="best")`** as the default. Matplotlib's `best` autoplaces into the emptiest quadrant; for most simple plots with a free corner that's the right answer.

**Multi-panel layouts, twin-axis plots with mixed chart types (bars + line, bars + fill), and symmetric/diverging layouts → below or outside the figure as the default.** `loc="best"` finds an empty *axes* corner, not an empty *figure* corner, so on these layouts it reliably plants the legend on top of one panel or one series. Anchor below the whole figure with `fig.legend`, or below a single axes with `bbox_to_anchor`:

```python
# Below the whole figure (multi-panel composition):
fig.legend(loc="lower center", bbox_to_anchor=(0.5, -0.02),
           ncol=N, frameon=False)

# Below a single axes (twin-axis mixed-type, tornado, etc.):
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18),
          ncol=N, frameon=False)
```

**Dense scatter / heatmaps that fill the whole frame → outside, right of the axes**:

```python
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
```

Outside / below is not the default for simple plots — over-eager outside placement steals up to 25% of the figure area and shrinks the data region. But for multi-panel, mixed-type, and symmetric layouts it *is* the default; `loc="best"` reliably misbehaves there.

**Deduplicate** when a series might be drawn twice (e.g., looping over groups and calling `plot` per row):

```python
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys())
```

**Size-encoded legends** (bubble charts, density-weighted scatter) follow the same rule: prefer the emptiest data quadrant; go outside only when every corner is busy. See `chart-types.md` → bubble recipe for the reference-value pattern.

**Direct labels are an alternative to a legend, not a supplement.** If you label each line at its endpoint, drop the legend entirely. Two labels for the same series is clutter. But never drop both — a multi-series chart without any series key is a defect.

Direct in-plot labels (end-of-line annotations, in-region text on a shaded area, name-next-to-bubble) work well only when the labelled items are *well-spaced* — single curves, isolated regions, or scatter points with visible gaps. When lines cluster, regions abut, or points crowd, in-place labels collide and the chart becomes unreadable; fall back to a legend in that case.

**Density defaults — keep the legend small.** Legends should never eat more than ~15% of the figure width/height. For dense legends, drop legend font to 8pt and tighten:

```python
ax.legend(fontsize=8, labelspacing=0.4, handletextpad=0.5, borderpad=0.4)
```

When labels are long enough that a single-column legend dominates the figure, set `ncol=2` (or shorten the label text in code, e.g. parenthetical sub-clauses moved to a footnote). When even a 2-column in-axes legend would still steal data area — typically when entries are many or labels are long — anchor the legend below the figure instead (see `fig.legend(loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=N, frameon=False)` above).

---

## Tick formatters

When axis values would otherwise render as long raw numbers (≥ 1k), use a custom formatter that abbreviates with magnitude suffixes. Readers parse "5k" or "2.3M" much faster than "5000" or "2,300,000".

```python
from matplotlib.ticker import FuncFormatter

def magnitude_format(x, _pos):
    if abs(x) >= 1e9: return f"{x/1e9:g}B"
    if abs(x) >= 1e6: return f"{x/1e6:g}M"
    if abs(x) >= 1e3: return f"{x/1e3:g}k"
    return f"{x:g}"

ax.xaxis.set_major_formatter(FuncFormatter(magnitude_format))
```

When the ticks visually carry the unit (currency prefix, magnitude suffix), drop the verbose unit-tag from the axis label — they would be redundant. Prepend a currency symbol or unit prefix inside the formatter when the description calls for one.

If you add a custom tick (an extra labelled year, a "Total" marker, a named reference point), check whether it sits close enough to a regular tick that the labels overlap. Drop the colliding regular tick only when the overlap is visible — don't pre-emptively thin a tick set that renders fine.

---

## Source citation

If the data file or the description references a source (publication, dataset name, organisation), include that attribution on or below the figure as reference information. A small caption-style text element under the axes (via `fig.text(...)`) is the most common placement; in-axes annotation works for inline mentions tied to a specific point. Choose font size, colour, and placement consistent with the rest of the figure styling — don't let the source line compete with the title.

---

## Annotation placement

Place annotations *inside* the axes whenever possible — `ax.annotate(name, xy=(x, y), xytext=(8, 0), textcoords="offset points")` with a small in-axis offset keeps the plot area intact.

**Off-axis annotation arrows only when the labelled point is genuinely outside the visible range** (a clipped outlier, an off-scale extreme). Even then, anchor the label *close to the edge* — extending it far outside the frame forces matplotlib (via `bbox_inches="tight"`) to enlarge the canvas and shrink the data area accordingly. A long lead-line is rarely worth the lost plot room.

---

## Axis padding

For scatter and bubble plots, end with:

```python
ax.margins(0.05)
```

so the outermost points are not clipped against the axis spine. Default matplotlib will draw the edge through the centre of an edge marker — large bubbles get sliced in half. The 5% margin adds enough headroom without making the plot look loose.

For categorical bars and line charts with their own explicit x-limits, `ax.margins` is unnecessary — your `set_xlim` already controls the framing.

---

## Layout

Always end with:

```python
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
```

`tight_layout()` resolves overlapping labels; `bbox_inches="tight"` trims the outer whitespace. For multi-panel figures with a shared title, use `plt.subplots_adjust(top=0.92)` after `tight_layout()` to leave room for `fig.suptitle(...)`.

---

## Multi-panel layout

When the description calls for multiple sub-plots (a main chart with side panels, a comparison grid, a chart plus an inset), compose them in **one figure** via `gridspec` and a single `savefig` call. Skill output is a single PNG — never emit multiple plot files.

```python
fig = plt.figure(figsize=(8, 5))
gs = fig.add_gridspec(
    nrows=2, ncols=3,
    height_ratios=[3, 1],   # main row tall, secondary row short
    width_ratios=[2, 1, 1], # main panel wider than side panels
)
ax_main  = fig.add_subplot(gs[0, 0])
ax_side1 = fig.add_subplot(gs[0, 1])
ax_side2 = fig.add_subplot(gs[0, 2])
ax_bot   = fig.add_subplot(gs[1, :])  # spans all columns

# Each subplot keeps its own title pad and legend anchor:
for ax in (ax_main, ax_side1, ax_side2, ax_bot):
    ax.set_title(..., pad=8)

fig.suptitle("Overall title", y=0.98)
fig.subplots_adjust(top=0.92, hspace=0.35, wspace=0.30)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
```

Key points:
- `top=0.92` in `subplots_adjust` leaves room for `fig.suptitle(...)` — otherwise the suptitle collides with the top row of panels.
- `hspace` / `wspace` control the gap between panels. 0.30–0.40 is a good starting range; tighten only if panels feel disconnected.
- Each panel's legend stays anchored to *that panel's axes*, not the figure — `ax_main.legend(...)`, not `fig.legend(...)`. Per-panel anchoring prevents a stray legend from drifting across the figure when sizes change.
- Don't call `plt.tight_layout()` *and* `subplots_adjust()` — pick one. `subplots_adjust` gives explicit control; `tight_layout` is automatic but can fight your `top=0.92` setting.

---

## Headless execution

Set the backend before importing pyplot when running in environments without a display:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

This avoids `_tkinter`/`Qt` errors when the script runs in a sub-agent or CI.

---

## Quick checklist before saving

- [ ] `figsize` matches the target column width
- [ ] Font sizes set globally via `rcParams`
- [ ] Title and both axis labels present, units included
- [ ] Legend present when there is more than one series
- [ ] Legend text is not clipped and does not cover essential data
- [ ] Axis scales match `figure-spec.md`
- [ ] Category order and color mapping match `figure-spec.md`
- [ ] Required annotations are present
- [ ] Unrequested overlays, labels, and fitted lines are absent
- [ ] Top/right spines hidden (unless polar / heatmap)
- [ ] `dpi=300`, `bbox_inches="tight"` on savefig
- [ ] `matplotlib.use("Agg")` if running headless
