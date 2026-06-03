# OWID Chart-Name-Only Rules

Use this reference when the task provides an Our World in Data style CSV plus a chart name or short metadata text, but no detailed figure brief.

## Intake

Before writing `figure-spec.md`:

1. Read the CSV header and the first 10 rows.
2. Read any same-stem `.txt` metadata file if available.
3. Identify the row type:
   - country rows
   - regional aggregate rows
   - world aggregate rows
   - annotation rows or annotation columns
4. Identify the target year or year range from the chart name, metadata, or data.
5. Decide whether the figure is a time series, stacked area, scatter, or bubble chart from the chart name and variable set.

Do not aggregate, filter, or replace entities until the decision is written in `figure-spec.md`.

## Entity Selection

- If the chart name says "by region", use regions only if the CSV contains region rows or region labels. Do not drop named subregions that the metadata identifies as important.
- If the chart name names countries or uses a country-level comparison (`vs. GDP per capita`, `life expectancy vs. GDP per capita`), use country rows and exclude aggregate rows such as `World`, `Asia`, `Europe`, and income groups.
- If the metadata lists annotation entities, use those entities as the first candidates for labels.
- Do not convert a country-level chart into a region-level chart because there are too many points. Use a bubble/scatter with limited labels instead.
- Do not silently drop rows with missing values. Record the filter in `figure-spec.md` and keep the plotted row count auditable.

## Scale Defaults

These are semantic defaults for common OWID chart families. Still record the final choice in `figure-spec.md`.

- GDP per capita on an axis: usually log scale.
- CO2 emissions per capita vs. GDP per capita: x-axis log; y-axis often log in OWID reference charts. Check metadata/reference wording and use log y when the reference uses logarithmic ticks.
- Life expectancy vs. GDP per capita: x-axis log, y-axis linear.
- Long-run emissions time series: x-axis linear year, y-axis linear unless metadata explicitly says log.
- Share/coverage time series: y-axis 0-100 percent linear.

Use matplotlib axis scales (`ax.set_xscale("log")`, `ax.set_yscale("log")`), not manual log transforms with relabelled ticks.

## Labels and Legends

- Prefer direct labels for a small set of named endpoint lines when lines are well-spaced.
- Use a legend when endpoint labels would overlap.
- For bubble/scatter charts, use one color legend for regions and one size legend for population only if population is part of the spec.
- Label only the entities listed in metadata or a compact set of representative/outlier countries. Do not label every point.
- Check that legends are not clipped. If a right-side legend is clipped, move it below or increase right margin before saving.

## Stacked Area Charts

- Preserve the requested entity breakdown. If metadata or reference text separates China, India, United States, European Union, aviation, or shipping, do not collapse them into broad continents unless the chart name explicitly asks for continents only.
- The stacked total should match the entities in scope. Do not mix country rows and region rows in the same stack unless the metadata defines that decomposition.
- Put the series order in `figure-spec.md`. Use a stable order that makes the stack readable and keeps small series visible.

## Audit Questions

Before final status:

- Does the chart use the same entity level as the chart name and metadata?
- Did any country/region/entity get dropped without an explicit filter?
- Do axis scales match the OWID chart family and metadata?
- Are population bubble sizes normalized but not so large that they cover the pattern?
- Are labels limited, readable, and tied to named entities or outliers?
- Does the source note cite OWID and the dataset source when available?
