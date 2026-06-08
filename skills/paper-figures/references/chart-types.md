# Chart-Type Recipes

One concise matplotlib idiom per supported chart type. Each recipe assumes you have already applied the defaults from `publication-style.md` (sans-serif, sizes, hidden top/right spines, `Agg` backend).

Snippets show only the *plotting* call, not data loading or savefig — wrap them in the standard skeleton:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("data.csv")
fig, ax = plt.subplots(figsize=(3.5, 2.6))

# <recipe goes here>

ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
```

---

## Contents

- [Line](#line)
- [Bar (vertical)](#bar-vertical)
- [Bar (horizontal)](#bar-horizontal)
- [Grouped / stacked bar](#grouped--stacked-bar)
- [Tornado](#tornado)
- [Scatter](#scatter)
- [Bubble](#bubble)
- [Histogram](#histogram)
- [KDE (density)](#kde-density)
- [Box plot](#box-plot)
- [Violin plot](#violin-plot)
- [Pie](#pie)
- [Ring (donut)](#ring-donut)
- [Phase diagram](#phase-diagram)
- [Heatmap](#heatmap)
- [Area / stacked area](#area--stacked-area)
- [Twin / shared axes](#twin--shared-axes)
- [Multi-panel composition](#multi-panel-composition)
- [3D plots](#3d-plots)

---

## Line

```python
for col in df.columns[1:]:
    ax.plot(df["x"], df[col], label=col, linewidth=1.5)
ax.set_xlabel("X (units)")
ax.set_ylabel("Y (units)")
ax.legend()
```

Use markers (`marker="o", markersize=3`) only when data points are few enough to be individually meaningful.

When the x axis is a year, make sure the **last data year actually appears on a tick**. Default tick locators often round down (data through 2022 ends up with 2020 as the rightmost tick), which makes the chart look out of date.

```python
from matplotlib.ticker import MaxNLocator
ax.set_xlim(df["year"].min(), df["year"].max())
ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune=None))
```

If the locator still skips the endpoint, force it explicitly with `ax.set_xticks([... , df["year"].max()])`.

**Distinguish series with linestyles** when:

(a) **two series share a colour family and play different roles** — set the linestyle explicitly and key the legend by linestyle, not colour; OR

(b) **one series is an aggregate or baseline alongside its member series** — make the aggregate visually distinct with a dashed pattern or a heavier weight so the eye separates the "overall" curve from the per-member curves.

```python
ax.plot(x, y_main, color="tab:blue", linestyle="-",  label="Main")
ax.plot(x, y_alt,  color="tab:blue", linestyle="--", label="Alt")
ax.legend()
```

For monochrome-friendly figures or many overlapping curves, cycling `linestyle=["-", "--", ":", "-."]` alongside the colour cycle keeps the curves discriminable even when printed in greyscale.

---

## Bar (vertical)

```python
ax.bar(df["category"], df["value"], color="tab:blue", edgecolor="none")
ax.set_ylabel("Value (units)")
ax.tick_params(axis="x", rotation=30)
```

Rotate x-tick labels (`rotation=30`, `ha="right"`) when categories are long enough to overlap.

**Keep small bars visible.** When the data spans many orders of magnitude, tiny bars vanish into the axis. Annotate their values inline with `ax.bar_label(...)`, or pass `edgecolor=..., linewidth=0.8` to the `bar(...)` call so near-zero values are still drawn as a thin line at the baseline.

---

## Bar (horizontal)

```python
ax.barh(df["category"], df["value"], color="tab:blue", edgecolor="none")
ax.set_xlabel("Value (units)")
ax.invert_yaxis()  # so the first row appears at the top
```

Use horizontal bars when category names are long or there are more than ~8 categories.

---

## Grouped / stacked bar

**Grouped** (side-by-side):
```python
import numpy as np
x = np.arange(len(df))
width = 0.35
ax.bar(x - width/2, df["series_a"], width, label="A")
ax.bar(x + width/2, df["series_b"], width, label="B")
ax.set_xticks(x, df["category"])
ax.legend()
```

**Stacked**:
```python
ax.bar(df["category"], df["a"], label="A")
ax.bar(df["category"], df["b"], bottom=df["a"], label="B")
ax.legend()
```

---

## Tornado

A horizontal grouped bar centered on zero — one scenario extends left (negative), one right (positive), one row per category.

```python
ax.barh(df["year"], -df["low_scenario"], color="tab:blue",
        edgecolor="black", linewidth=0.4, label="Low")
ax.barh(df["year"],  df["high_scenario"], color="tab:orange",
        edgecolor="black", linewidth=0.4, label="High")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Value (units)")
ax.invert_yaxis()
# Tornado / diverging-bar charts have no empty corner — anchor the legend
# below the chart, outside the data region. `loc="best"` would land on top
# of the longest bars.
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08),
          ncol=2, frameon=True)
```

If both scenario columns are stored as positive magnitudes, negate the "low" side at plot time as above. If they are already signed, plot them directly.

Audit rules:
- The category order must match the description. For year-based tornado charts, "1997 at the top to 2022 at the bottom" means call `invert_yaxis()` after plotting in ascending year order.
- The center zero line must be visible and must not be hidden by bars or gridlines.
- The left and right scenarios must keep their semantic colors throughout the figure and legend.
- Do not add a y-axis label such as "Year" unless the description asks for it; the tick labels already carry the year.
- The legend position should follow the description or reference. If unspecified, place it outside the data region; below the chart is a safe default.

---

## Scatter

```python
ax.scatter(df["x"], df["y"], s=20, alpha=0.7, edgecolor="none")
ax.set_xlabel("X (units)")
ax.set_ylabel("Y (units)")
ax.margins(0.05)  # don't clip outermost points against the spines
```

For grouped scatter, loop over groups so the legend works:
```python
for name, sub in df.groupby("group"):
    ax.scatter(sub["x"], sub["y"], s=20, alpha=0.7, label=name)
ax.legend()
```

---

## Bubble

A scatter where marker size encodes a third numeric variable. Reach for it whenever the data has three (or four, counting color) numeric dimensions you want to preserve — falling back to plain scatter quietly drops a dimension.

**Size encodes exactly one variable.** Don't blend two columns into the marker size (no `s = col_a * col_b`, no concatenated normalisations of two metrics). If the description hints at two size-relevant variables, pick the one the brief emphasises and use colour, transparency, or a second chart channel for the other.

**Sizing**: always normalize, then pad the axes so large bubbles aren't clipped in half by the frame:

```python
sizes = df["weight"] / df["weight"].max() * 400  # area scale, ~marker pts
ax.scatter(df["x"], df["y"], s=sizes, alpha=0.6,
           edgecolor="white", linewidth=0.5)
ax.margins(0.08)  # extra headroom — the biggest bubbles need it
```

**Size legend** — 3 reference values keyed to **round, semantic magnitudes** that bracket the data range. For natural-unit variables (population, GDP, count) human-readable round numbers like `100M / 500M / 1B` are much easier to scan than precise quantiles like `87,453,210`.

**One legend per visual variable.** Each channel — size, color, shape — gets at most one legend entry. If color encodes region and size encodes population, build one size legend (3 round magnitudes for population) plus one color legend (regions); never a single legend whose handles vary in both size and color, and never a second size legend keyed off the categorical axis. Mixed handles read as "size means region" and silently re-encode a variable that's actually carried by color.

```python
# Pick round magnitudes that span the actual data range, not quantiles.
# For populations: 100M / 500M / 1B. For currencies: $1k / $1M / $1B.
# For counts: 100 / 1k / 10k. For percentages: 1 / 10 / 50.
ref_vals   = [1e8, 5e8, 1e9]
ref_labels = ["100 million", "500 million", "1 billion"]
handles = [
    ax.scatter([], [], s=v / df["weight"].max() * 400,
               c="lightgray", edgecolor="white", label=lbl)
    for v, lbl in zip(ref_vals, ref_labels)
]
```

**Placement: empty quadrant first, outside as fallback.** Most bubble scatters have one corner with few or no points — that's the right home for the size legend. Only anchor outside the axes when every corner is busy.

```python
# First choice: legend inside an empty quadrant
ax.legend(handles=handles, title="Weight",
          loc="lower right", frameon=False,
          labelspacing=1.6, borderpad=0.8)

# Fallback (when the data fills every corner): outside, bottom-left
# ax.legend(handles=handles, title="Weight",
#           loc="lower left", bbox_to_anchor=(1.02, 0),
#           frameon=False, labelspacing=1.6, borderpad=0.8)
```

A size legend anchored outside the axes typically eats 20–25% of the figure width and shrinks the data area — only worth it when there's no in-axes home.

**Do not add point labels by default.** Bubble charts often have dense clusters; unsolicited labels are the fastest way to make the figure unreadable. Add labels only when:
- the description names specific points to label,
- `figure-spec.md` lists a small `required_annotations` set, or
- the task is chart-name-only and the brief explicitly chooses a limited set of labelled points for interpretability.

When you choose labels yourself, cap them at 8-10, prefer high-salience points (largest bubbles, named outliers, or entities named in the metadata), and record the choice in `figure-spec.md`. Never label every point.

**Point labels** — when the description names specific points to label (or you're picking the top-N as above), place them next to the bubble with a fixed offset and *match the bubble's color*:

```python
for name in LABEL_POINTS:
    row = df[df["name"] == name]
    if row.empty:
        continue
    ax.annotate(name,
                xy=(row["x"].iat[0], row["y"].iat[0]),
                xytext=(8, 0), textcoords="offset points",
                ha="left", va="center",
                color=color_for(row["group"].iat[0]),
                fontsize=8)
```

Same-color text reads as "belongs to this bubble" without needing a connector line. Only label a handful of named points — labelling everything turns the chart into noise.

**Clipped / off-scale bubbles**: when one or two bubbles sit at or past the axis range, annotate them rather than silently dropping or letting them get sliced. Two patterns:

```python
# Partially clipped (bubble centre on-axis, edge spills beyond):
# Place the label adjacent to the visible part of the bubble, no arrow needed.
ax.annotate(point_name,
            xy=(point_x, point_y),
            xytext=(6, 6), textcoords="offset points",
            ha="left", fontsize=8, color=point_color)

# Fully off-scale (point falls outside the visible range):
# Anchor the label just inside the nearest edge; short arrow points outward.
ax.annotate(f"{point_name} (off scale, value {actual_value})",
            xy=(ax.get_xlim()[0], ax.get_ylim()[0]),
            xytext=(20, 20), textcoords="offset points",
            fontsize=8, color="dimgray",
            arrowprops=dict(arrowstyle="->", color="dimgray", lw=0.6))
```

Silent omission is a defect — invisible-without-warning is the worst outcome. Keep the label close to the edge; long lead-lines outside the frame expand the canvas (via `bbox_inches="tight"`) and shrink the plot area.

**This rule recurs on bubble plots.** A point that didn't survive a `dropna`, a row that went to `-inf` after a `log10` transform, a country/category filtered out by an axis-range cap — all common failure modes. Before saving the figure, check `len(df_plotted) == len(df_input)` (minus any rows the description explicitly excluded). If you dropped a row, annotate it.

**No unrequested analytical overlays.** Do not add diagonal equality lines, regression fits, trend lines, convex hulls, or density contours unless the description asks for them or `figure-spec.md` lists them under `required_annotations`.

**Log-scale audit.** If either axis is log-scaled, set the matplotlib scale with `ax.set_xscale("log")` or `ax.set_yscale("log")` rather than pre-transforming the values and relabelling the ticks manually. For OWID-style GDP/emissions scatterplots, check the metadata and reference wording carefully; many use log scales on both axes.

---

## Histogram

```python
ax.hist(df["value"], bins=30, color="tab:blue", edgecolor="white")
ax.set_xlabel("Value (units)")
ax.set_ylabel("Count")
```

Use `density=True` to plot probability density instead of counts. Pick `bins` from the data shape: 20-40 is a good default; less when data are sparse.

**Never hide the x-axis ticks on a histogram.** The x-axis ticks ARE the bin boundaries — without them the reader can't read off where any bar sits. Don't call `ax.set_xticks([])` or `ax.tick_params(bottom=False)` on a histogram regardless of style preferences.

---

## KDE (density)

Pure matplotlib doesn't ship a KDE — use `scipy.stats.gaussian_kde`:

```python
from scipy.stats import gaussian_kde
import numpy as np

values = df["value"].dropna().values
kde = gaussian_kde(values, bw_method="scott")
xs = np.linspace(values.min(), values.max(), 400)
ax.plot(xs, kde(xs), color="#2c7bb6", linewidth=2)
ax.fill_between(xs, kde(xs), alpha=0.3, color="#2c7bb6")
ax.set_xlabel("Value (units)")
ax.set_ylabel("Density")
```

---

## Box plot

```python
data = [df[df["group"] == g]["value"].values for g in df["group"].unique()]
ax.boxplot(data, labels=df["group"].unique(), patch_artist=True,
           boxprops=dict(facecolor="tab:blue", alpha=0.4),
           medianprops=dict(color="black"))
ax.set_ylabel("Value (units)")
```

Use `showfliers=False` when outliers dominate the y-range and the description focuses on the body of the distribution.

---

## Violin plot

```python
data = [df[df["group"] == g]["value"].values for g in df["group"].unique()]
parts = ax.violinplot(data, showmeans=False, showmedians=True)
ax.set_xticks(range(1, len(data) + 1), df["group"].unique())
ax.set_ylabel("Value (units)")
```

For colored violins, iterate `parts["bodies"]` and call `set_facecolor`.

---

## Pie

```python
ax.pie(df["value"], labels=df["category"], autopct="%1.1f%%",
       startangle=90, counterclock=False, textprops={"color": "black"},
       colors=plt.cm.tab10.colors[:len(df)])
ax.axis("equal")
```

Pie charts work poorly above ~6 slices. If the description has more, switch to horizontal bar.

Preserve category order. If the description lists categories in a specific order, plot slices in that order even if sorting by value would look cleaner. If the description or reference implies a slice at the top, set `startangle` to match it; otherwise use `startangle=90` and record that choice in `figure-spec.md`.

For percentage text, black is the default because it remains legible across light pastel slices. Use white text only on consistently dark wedges and only after checking contrast. When labels are outside the pie, reserve enough margin so labels are not clipped by `bbox_inches="tight"`.

---

## Ring (donut)

A pie with a hole — same data, but a white circle on top.

```python
wedges, _, _ = ax.pie(df["value"], labels=df["category"], autopct="%1.1f%%",
                      startangle=90, counterclock=False,
                      textprops={"color": "black"},
                      wedgeprops=dict(width=0.4, edgecolor="white"))
ax.axis("equal")
```

`width=0.4` controls ring thickness (1.0 = full pie, smaller = thinner ring).

Audit rules:
- The number of slices must equal the number of categories in scope.
- Slice order and direction must follow the description/reference when provided.
- Labels and percentages must both be readable. If long labels collide, move the legend outside and keep only percentages inside the ring, but do not drop categories.
- Do not rotate the chart arbitrarily between runs. Put the chosen `startangle` in `figure-spec.md`.

---

## Phase diagram

Phase diagrams are data-driven scientific diagrams, not decorative regions. The boundary curves must come from the specified data columns.

Required audit points:
- Confirm which columns define each phase boundary before plotting. Do not infer boundary shapes from region names.
- Use logarithmic pressure scaling when the pressure range spans pascals to megapascals or the description requests log scale.
- If dual axes are requested, define explicit conversion functions, for example Kelvin to Celsius and pascals to bar/mbar.
- Mark special points with exact coordinates from the description/data: triple point, critical point, freezing point, boiling point.
- Region fills must sit behind boundary lines (`zorder` lower than lines) and must not hide labels or gridlines.
- Red reference lines must intersect the correct axis values and be annotated with both temperature and pressure when requested.

Skeleton:

```python
fig, ax = plt.subplots(figsize=(5.0, 3.8))
ax.set_yscale("log")
ax.plot(df["boundary_temp_K"], df["boundary_pressure_Pa"],
        color="black", linewidth=1.2, label="Liquid-gas boundary")
ax.plot(df["solid_liquid_temp_K"], df["solid_liquid_pressure_Pa"],
        color="black", linestyle="--", linewidth=1.0,
        label="Solid-liquid boundary")
ax.axvline(273.15, color="red", linewidth=0.9)
ax.axvline(373.15, color="red", linewidth=0.9)
ax.scatter([273.16, 647.396], [611.657, 22.064e6],
           color="black", s=20, zorder=5)
ax.set_xlabel("Temperature (K)")
ax.set_ylabel("Pressure (Pa)")
```

---

## Heatmap

```python
import numpy as np

matrix = df.pivot(index="row", columns="col", values="value").values
im = ax.imshow(matrix, cmap="viridis", aspect="auto")
ax.set_xticks(range(matrix.shape[1]), df["col"].unique())
ax.set_yticks(range(matrix.shape[0]), df["row"].unique())
fig.colorbar(im, ax=ax, label="Value")
```

For diverging data centered at zero, use `cmap="RdBu_r"` and pass `vmin=-vmax, vmax=vmax`.

---

## Area / stacked area

```python
ax.stackplot(df["x"], df["a"], df["b"], df["c"],
             labels=["A", "B", "C"], alpha=0.7)
ax.set_xlabel("X (units)")
ax.set_ylabel("Y (units)")
ax.legend(loc="upper left")
```

Order the series so the most stable goes on the bottom (smallest variation = strongest visual anchor).

---

## Twin / shared axes

**Twin y-axis** (two series, different units, same x):
```python
fig, ax1 = plt.subplots(figsize=(5, 3))
ax1.plot(df["year"], df["price"], color="tab:blue", label="Price")
ax1.set_ylabel("Price ($)", color="tab:blue")
ax2 = ax1.twinx()
ax2.plot(df["year"], df["volume"], color="tab:orange", label="Volume")
ax2.set_ylabel("Volume", color="tab:orange")
```

Color the y-labels and tick labels to match each series — without that, readers can't tell which axis a curve belongs to.

**Mixed-type twin axes share a visual baseline.** When the two y-axes carry *different* chart types (bars on one side, line/fill on the other), don't set each `ylim` independently — the axis whose data starts at zero will end up with its zero floating above the x-axis line, breaking the visual baseline.

```python
# Pattern A — bars non-negative, both axes anchor at 0:
ax1.set_ylim(0, max(bar_data) * 1.1)
ax2.set_ylim(0, max(line_data) * 1.1)

# Pattern B — bars signed; scale ax2 so its visual bottom matches ax1's data-zero:
ax1.set_ylim(bar_min, bar_max)
ratio = (0 - bar_min) / (bar_max - bar_min)
ax2_low = line_min - ratio * (line_max - line_min) / (1 - ratio)
ax2.set_ylim(ax2_low, line_max)
```

**Prefix axis labels with the plot type** when the two axes carry different chart types — readers need a fast way to match each curve/bar to its scale:

```python
ax1.set_ylabel("Bar: <metric> (units)")
ax2.set_ylabel("Line: <metric> (units)")
```

**Shared axes** (multi-panel comparison):
```python
fig, axes = plt.subplots(2, 2, figsize=(7, 5), sharex=True, sharey=True)
```

`sharex=True` / `sharey=True` ties zooming and ticks across panels.

**Broken axis** (huge range gap): use two stacked axes with `ax.spines["bottom"].set_visible(False)` on the top one and `ax.spines["top"].set_visible(False)` on the bottom one, plus diagonal cut marks. Only do this when a single linear or log axis genuinely cannot show the data.

---

## Multi-panel composition

When the description calls for several panels in one figure — a main chart with side panels, a 2×N comparison grid, or a chart with one or more insets — compose them via `gridspec` in a single figure and a single `savefig`.

```python
fig = plt.figure(figsize=(8, 5))
gs = fig.add_gridspec(
    nrows=2, ncols=3,
    height_ratios=[3, 1],      # main row tall, secondary row short
    width_ratios=[2, 1, 1],    # main panel wider than side panels
)
ax_main  = fig.add_subplot(gs[0, 0])
ax_side1 = fig.add_subplot(gs[0, 1])
ax_side2 = fig.add_subplot(gs[0, 2])
ax_bot   = fig.add_subplot(gs[1, :])    # spans all three columns

# ... draw on each axes with its own title/legend ...

for ax in (ax_main, ax_side1, ax_side2, ax_bot):
    ax.set_title(ax.get_title(), pad=8)
    ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("Overall figure title", y=0.98)
fig.subplots_adjust(top=0.92, hspace=0.35, wspace=0.30)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
```

Key points:
- One `savefig` per task. Don't emit multiple PNGs and ask the harness to stitch.
- `top=0.92` in `subplots_adjust` leaves room for `fig.suptitle(...)` — otherwise the suptitle collides with the top row.
- Each panel's legend stays anchored to *that panel's axes*, not the figure. `ax_main.legend(...)`, not `fig.legend(...)`.
- Don't combine `tight_layout()` and `subplots_adjust()` — `subplots_adjust` gives explicit control; `tight_layout` will fight the `top=0.92` constraint.
- Use `wspace` / `hspace` to control inter-panel gaps (0.25–0.40 is a good range). Tight panels (`wspace=0.05`) only when they share an axis (`sharey=True`).

**`sharex` / `sharey` propagate axis-stripping across panels.** If one panel strips its ticks (e.g. an axis-free statistical summary placed above a histogram, or any panel where the description explicitly removes axes), do **not** use `sharex=True` / `sharey=True` with its neighbours — the strip will silently propagate and the other panels will lose their ticks too. Either stack the panels without `sharex`/`sharey`, or strip the axis on the specific panel after creation (`ax_stripped.tick_params(bottom=False, labelbottom=False)`) so neighbours keep their own ticks. After any subplot tick adjustment, verify each panel that needs ticks still has them.

**Multi-layer single-axis figures** (waterfall + area + inset pies, bars + lines + annotations) should use a fixed layering plan:
1. Draw large background layers first (`fill_between`, stacked areas) with low alpha.
2. Draw primary marks second (bars, waterfall deltas, main lines).
3. Draw annotations and insets last.
4. Keep each visual channel in only one legend. If there are multiple chart types, use separate compact legends with clear titles.
5. Use `inset_axes` or `fig.add_axes` for pies positioned by year. Do not approximate their position with pixel arithmetic.
6. Before saving, check that the primary chart remains readable after the insets and legends are added.

For waterfall + secondary consumption area:

```python
fig, ax1 = plt.subplots(figsize=(7.0, 4.5))
ax2 = ax1.twinx()
ax2.fill_between(years, urban_consumption, alpha=0.18,
                 color="tab:blue", label="Urban consumption")
ax2.fill_between(years, rural_consumption, alpha=0.18,
                 color="tab:orange", label="Rural consumption")
ax1.bar(x - width / 2, urban_import_delta, width,
        color=urban_colors, label="Urban import change", zorder=3)
ax1.bar(x + width / 2, rural_import_delta, width,
        color=rural_colors, label="Rural import change", zorder=3)
ax1.set_ylabel("Imports (kg)")
ax2.set_ylabel("Consumption (kg)")
```

---

## 3D plots

3D figures are inherently harder to read than 2D — depth perception via flat projection is lossy. Prefer 2D when the data permits. When a description genuinely calls for 3D (a 3D surface, a 3D scatter cloud, a waterfall of time series), follow these guardrails:

```python
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers projection)
fig = plt.figure(figsize=(7, 5))                    # minimum useful 3D size
ax = fig.add_subplot(111, projection="3d")
# 3D axes default to leaving big margins around the projected box; reclaim them:
fig.subplots_adjust(left=0.05, right=0.95, bottom=0.10, top=0.92)
ax.set_title(title, pad=8)                          # easy to forget on 3D — do not skip
```

The default 3D rendering wastes ~30% of the figure area as white margin and crops the title against the top of the canvas — both `subplots_adjust(...)` and an explicit `set_title(..., pad=8)` are necessary, not optional.

- **Prefer 3D line or surface over 3D scatter markers.** Markers in 3D rapidly become unreadable as occlusion and depth ambiguity grow — `ax.plot(...)` and `ax.plot_surface(...)` carry meaningful shape information that `ax.scatter(...)` in 3D usually loses.
- **Pick colours that stay distinct under 3D rotation.** Muddy palettes (mixed darks: navy + green + brown + grey + cyan) blur together under the dimmer shading 3D applies. Stick to `tab10` or a colourblind-safe palette (Okabe-Ito) where each entry is well-separated in hue and brightness.
- **When a tick set is suppressed (common on 3D waterfall y/z axes), label each series at its endpoint with its value.** End-of-curve labels recover the information the missing ticks would have carried, without restoring tick clutter.
- **Legend below the chart, horizontal.** 3D plots have no usable "best" corner — the data fills the projected box. Anchor the legend horizontally below the axes:
  ```python
  ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05),
            ncol=min(len(series), 4), frameon=False)
  ```
- **`ax.view_init(elev=…, azim=…)` is your friend.** The matplotlib default (elev=30, azim=-60) is fine for surfaces but suboptimal for 3D lines. Adjust only when the description suggests a viewing angle, or when the default visibly hides important data.
