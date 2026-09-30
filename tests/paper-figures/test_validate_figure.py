"""Tests for skills/paper-figures/scripts/validate_figure.py.

Run from the repository root (needs pytest):
    pytest tests/paper-figures -q
"""

import re
import struct
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "paper-figures"
sys.path.insert(0, str(SKILL / "scripts"))

import validate_figure  # noqa: E402

PLOT_PY = """\
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2], [1, 2])
{extra}
ax.set_title("t")
ax.set_xlabel("x")
ax.set_ylabel("y")
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
"""

SPEC = """\
# Figure Spec

- chart_type: line
- data_sources: data.csv
- rows_in_scope: all
- data_columns: a, b
- x_axis:
{x_axis}
- y_axis:
  - field: b
  - label: B
  - unit: none
  - scale: linear
  - range: auto
- additional_axes:{additional_axes}
- series_or_categories: one
- category_order: n/a
- color_mapping: blue
- size_mapping: none
- legend: none
- required_annotations: none
- forbidden_elements: regression lines
- layout_constraints: single panel
- source_note: none
- assumptions: none
"""

X_AXIS_LINEAR = (
    "  - field: a\n  - label: A\n  - unit: none\n  - scale: linear\n  - range: auto"
)


def _png(width: int = 800, height: int = 600) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
    )


def run(tmp_path, capsys, *, spec: str, plot_extra: str = ""):
    (tmp_path / "plot.py").write_text(
        PLOT_PY.format(extra=plot_extra), encoding="utf-8"
    )
    (tmp_path / "plot.png").write_bytes(_png())
    (tmp_path / "figure-spec.md").write_text(spec, encoding="utf-8")
    code = validate_figure.main(["--output-dir", str(tmp_path)])
    return code, capsys.readouterr().err


def spec(x_axis: str = X_AXIS_LINEAR, additional_axes: str = " none") -> str:
    return SPEC.format(x_axis=x_axis, additional_axes=additional_axes)


def test_spec_with_nested_axis_fields_passes(tmp_path, capsys):
    code, err = run(tmp_path, capsys, spec=spec())
    assert err == ""
    assert code == 0


def test_template_in_skill_md_is_accepted_once_filled_in(tmp_path, capsys):
    skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    template = re.search(r"```markdown\n(# Figure Spec\n.*?)```", skill_md, re.S).group(
        1
    )
    filled = re.sub(r"(?m)^(\s*- scale):\s*$", r"\1: linear", template)
    filled = re.sub(r"(?m)^(\s+- \w+):\s*$", r"\1: value", filled)
    filled = re.sub(r"(?m)^(- (?!x_axis|y_axis)\w+):\s*$", r"\1: value", filled)
    code, err = run(tmp_path, capsys, spec=filled)
    assert err == ""
    assert code == 0


def test_log_scale_in_spec_without_log_call_is_an_error(tmp_path, capsys):
    code, err = run(tmp_path, capsys, spec=spec(X_AXIS_LINEAR.replace("linear", "log")))
    assert "x_axis spec requires log scale" in err
    assert code == 1


def test_log_scale_in_spec_with_log_call_passes(tmp_path, capsys):
    code, err = run(
        tmp_path,
        capsys,
        spec=spec(X_AXIS_LINEAR.replace("linear", "log")),
        plot_extra='ax.set_xscale("log")',
    )
    assert err == ""
    assert code == 0


def test_axis_missing_only_label_reports_only_label(tmp_path, capsys):
    code, err = run(
        tmp_path, capsys, spec=spec("  - field: a\n  - unit: none\n  - scale: linear")
    )
    assert "x_axis missing label" in err
    assert "x_axis missing scale" not in err
    assert "x_axis missing field" not in err
    assert code == 1


def test_axis_block_stops_at_next_top_level_key(tmp_path, capsys):
    code, err = run(
        tmp_path, capsys, spec=spec(additional_axes="\n  - field: c\n  - scale: log")
    )
    assert err == ""
    assert code == 0


def test_tab_indented_fields_under_space_indented_axis_are_read(tmp_path, capsys):
    text = spec().replace(
        "- x_axis:\n" + X_AXIS_LINEAR,
        "  - x_axis:\n\t- field: a\n\t- unit: none\n\t- scale: linear",
    )
    code, err = run(tmp_path, capsys, spec=text)
    assert "x_axis missing label" in err
    assert code == 1


# Characterisation of behaviour the fix must keep.


def test_axis_with_no_nested_fields_is_not_checked(tmp_path, capsys):
    text = spec().replace(X_AXIS_LINEAR + "\n", "")
    code, err = run(tmp_path, capsys, spec=text)
    assert "x_axis" not in err
    assert code == 0


def test_axis_with_inline_value_reports_missing_fields(tmp_path, capsys):
    text = spec().replace("- x_axis:\n" + X_AXIS_LINEAR, "- x_axis: a (linear)")
    code, err = run(tmp_path, capsys, spec=text)
    assert "x_axis missing field" in err
    assert code == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
