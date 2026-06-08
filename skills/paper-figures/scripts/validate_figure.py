#!/usr/bin/env python3
"""Lightweight structural validator for paper-figures outputs.

This script does not judge artistic quality. It checks the contract that the
skill can verify mechanically: required files, a valid PNG, a compact
figure-spec.md, savefig settings, and axis-scale consistency when the spec
requires log scales.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path


REQUIRED_SPEC_KEYS = [
    "chart_type",
    "data_sources",
    "data_columns",
    "x_axis",
    "y_axis",
    "series_or_categories",
    "legend",
    "required_annotations",
    "forbidden_elements",
    "assumptions",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def extract_axis_block(spec: str, axis_name: str) -> str:
    pattern = rf"(?ims)^\s*-\s*{re.escape(axis_name)}\s*:\s*(.*?)(?=^\s*-\s*[a-zA-Z0-9_]+:\s*|\Z)"
    match = re.search(pattern, spec)
    return match.group(1) if match else ""


def axis_requires_log(spec: str, axis_name: str) -> bool:
    block = extract_axis_block(spec, axis_name)
    return bool(re.search(r"(?im)^\s*-\s*scale\s*:\s*(log|log10|symlog)\b", block))


def has_log_call(code: str, axis: str) -> bool:
    if axis == "x_axis":
        patterns = [
            r"\.set_xscale\(\s*['\"]log",
            r"plt\.xscale\(\s*['\"]log",
        ]
    else:
        patterns = [
            r"\.set_yscale\(\s*['\"]log",
            r"plt\.yscale\(\s*['\"]log",
        ]
    return any(re.search(pattern, code) for pattern in patterns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--plot-py", type=Path)
    parser.add_argument("--plot-png", type=Path)
    args = parser.parse_args(argv)

    output_dir = args.output_dir
    plot_py = args.plot_py or output_dir / "plot.py"
    plot_png = args.plot_png or output_dir / "plot.png"
    spec_path = args.spec or output_dir / "figure-spec.md"

    errors: list[str] = []
    warnings: list[str] = []

    if not output_dir.exists():
        errors.append(f"output directory does not exist: {output_dir}")

    code = ""
    if not plot_py.exists():
        errors.append(f"missing plot.py: {plot_py}")
    else:
        code = read_text(plot_py)
        if "savefig" not in code:
            errors.append("plot.py does not call savefig")
        if not re.search(r"dpi\s*=\s*300", code):
            errors.append("savefig should set dpi=300")
        if "bbox_inches" not in code or "tight" not in code:
            errors.append('savefig should use bbox_inches="tight"')
        if "matplotlib.use" not in code:
            warnings.append("plot.py does not set a headless matplotlib backend")
        if not re.search(r"\.set_title\(|plt\.title\(", code):
            warnings.append("no title-setting call detected")
        if not re.search(r"\.set_xlabel\(|plt\.xlabel\(", code):
            warnings.append("no x-label-setting call detected")
        if not re.search(r"\.set_ylabel\(|plt\.ylabel\(", code):
            warnings.append("no y-label-setting call detected")

    if not plot_png.exists():
        errors.append(f"missing plot.png: {plot_png}")
    else:
        try:
            width, height = png_size(plot_png)
            if width < 300 or height < 200:
                errors.append(f"plot.png is too small: {width}x{height}")
        except ValueError as exc:
            errors.append(f"invalid plot.png: {exc}")

    spec = ""
    if not spec_path.exists():
        errors.append(f"missing figure spec: {spec_path}")
    else:
        spec = read_text(spec_path)
        for key in REQUIRED_SPEC_KEYS:
            if not re.search(rf"(?im)^\s*-\s*{re.escape(key)}\s*:", spec):
                errors.append(f"figure-spec.md missing required key: {key}")

        for axis_name in ("x_axis", "y_axis"):
            block = extract_axis_block(spec, axis_name)
            if not block:
                continue
            if not re.search(r"(?im)^\s*-\s*field\s*:", block):
                errors.append(f"{axis_name} missing field")
            if not re.search(r"(?im)^\s*-\s*label\s*:", block):
                errors.append(f"{axis_name} missing label")
            if not re.search(r"(?im)^\s*-\s*scale\s*:", block):
                errors.append(f"{axis_name} missing scale")

        if code:
            if axis_requires_log(spec, "x_axis") and not has_log_call(code, "x_axis"):
                errors.append(
                    "x_axis spec requires log scale but plot.py does not set xscale('log')"
                )
            if axis_requires_log(spec, "y_axis") and not has_log_call(code, "y_axis"):
                errors.append(
                    "y_axis spec requires log scale but plot.py does not set yscale('log')"
                )

    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in warnings:
        print(f"WARNING: {message}", file=sys.stderr)

    if errors:
        return 1

    print("PASS: structural checks passed")
    if warnings:
        print(f"PASS_WITH_WARNINGS: {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
