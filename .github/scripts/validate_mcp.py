#!/usr/bin/env python3
"""Validate the MCP server definitions in mcp/*.yaml against mcp/README.md."""

import glob
import re
import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = ["name", "label", "description", "tags", "transport"]
TRANSPORTS = ["stdio", "http", "streamable_http"]
STDIO_ONLY_FIELDS = ["command", "args"]
HTTP_ONLY_FIELDS = ["url", "headers"]
NAME_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# Every field in the README's Field Reference, with the type it must have.
FIELD_TYPES = {
    "name": str,
    "label": str,
    "description": str,
    "tags": list,
    "transport": str,
    "command": str,
    "args": list,
    "url": str,
    "headers": dict,
    "pip_package": str,
    "env": dict,
    "env_key": str,
    "env_hint": str,
    "env_optional": bool,
}
TYPE_NAMES = {str: "a string", list: "a list", dict: "a mapping", bool: "true or false"}


def validate_server(filepath: str) -> list[str]:
    """Validate a single server definition. Returns list of error messages."""
    stem = Path(filepath).stem

    try:
        data = yaml.safe_load(Path(filepath).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"{stem}: Invalid YAML — {e}"]

    if not isinstance(data, dict):
        return [f"{stem}: File is not a YAML mapping"]

    errors = []

    for field in REQUIRED_FIELDS:
        if not data.get(field):
            errors.append(f"{stem}: Missing required field '{field}'")

    # EvoScientist ignores fields it does not know, so a typo drops the value silently.
    for field in data:
        if field not in FIELD_TYPES:
            errors.append(f"{stem}: Unknown field '{field}'")

    for field, expected in FIELD_TYPES.items():
        if data.get(field) is not None and not isinstance(data[field], expected):
            errors.append(f"{stem}: '{field}' must be {TYPE_NAMES[expected]}")

    name = data.get("name")
    if isinstance(name, str) and name != stem:
        errors.append(f"{stem}: 'name' is {name!r} but must match the filename")
    if isinstance(name, str) and not NAME_RE.fullmatch(name):
        errors.append(f"{stem}: 'name' must be lowercase letters, digits and hyphens")

    transport = data.get("transport")
    if isinstance(transport, str) and transport not in TRANSPORTS:
        errors.append(
            f"{stem}: transport {transport!r} is not one of {', '.join(TRANSPORTS)}"
        )
    if transport == "stdio":
        if not data.get("command"):
            errors.append(f"{stem}: stdio transport needs 'command'")
        for field in HTTP_ONLY_FIELDS:
            if field in data:
                errors.append(
                    f"{stem}: '{field}' applies to http transports, not stdio"
                )
    if transport in ("http", "streamable_http"):
        if not data.get("url"):
            errors.append(f"{stem}: {transport} transport needs 'url'")
        for field in STDIO_ONLY_FIELDS:
            if field in data:
                errors.append(
                    f"{stem}: '{field}' applies to the stdio transport, not {transport}"
                )

    return errors


def main():
    server_files = sorted(glob.glob("mcp/*.yaml"))

    if not server_files:
        print("No server definitions found in mcp/*.yaml")
        sys.exit(1)

    all_errors = []
    for filepath in server_files:
        errors = validate_server(filepath)
        if errors:
            for e in errors:
                print(f"  ❌ {e}")
            all_errors.extend(errors)
        else:
            print(f"  ✅ {Path(filepath).stem}")

    print()
    if all_errors:
        print(
            f"❌ {len(all_errors)} error(s) in {len(set(e.split(':')[0] for e in all_errors))} server(s)"
        )
        sys.exit(1)
    else:
        print(f"✅ All {len(server_files)} servers passed validation")


if __name__ == "__main__":
    main()
