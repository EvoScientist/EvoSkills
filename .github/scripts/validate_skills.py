#!/usr/bin/env python3
"""Validate SKILL.md frontmatter for all skills in the repository."""

import glob
import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = ["name", "description", "allowed-tools", "metadata"]
REQUIRED_METADATA = ["author", "version", "tags"]


def extract_frontmatter(filepath: str) -> str | None:
    """Extract YAML frontmatter from a SKILL.md file."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None

    # Find the closing ---
    end = content.index("---", 3)
    return content[3:end].strip()


def validate_skill(filepath: str) -> list[str]:
    """Validate a single SKILL.md file. Returns list of error messages."""
    errors = []
    skill_name = Path(filepath).parent.name

    try:
        fm_text = extract_frontmatter(filepath)
    except (ValueError, FileNotFoundError) as e:
        return [f"{skill_name}: Failed to read frontmatter — {e}"]

    if not fm_text:
        return [f"{skill_name}: Missing YAML frontmatter (file must start with ---)"]

    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return [f"{skill_name}: Invalid YAML — {e}"]

    if not isinstance(data, dict):
        return [f"{skill_name}: Frontmatter is not a YAML mapping"]

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"{skill_name}: Missing required field '{field}'")

    # Check metadata sub-fields
    meta = data.get("metadata", {})
    if isinstance(meta, dict):
        for field in REQUIRED_METADATA:
            if field not in meta:
                errors.append(f"{skill_name}: Missing metadata field '{field}'")
    elif "metadata" in data:
        errors.append(f"{skill_name}: 'metadata' must be a mapping")

    return errors


def main():
    skill_files = sorted(glob.glob("skills/*/SKILL.md"))

    if not skill_files:
        print("No SKILL.md files found in skills/*/")
        sys.exit(1)

    all_errors = []
    for filepath in skill_files:
        skill_name = Path(filepath).parent.name
        errors = validate_skill(filepath)
        if errors:
            for e in errors:
                print(f"  ❌ {e}")
            all_errors.extend(errors)
        else:
            print(f"  ✅ {skill_name}")

    print()
    if all_errors:
        print(
            f"❌ {len(all_errors)} error(s) in {len(set(e.split(':')[0] for e in all_errors))} skill(s)"
        )
        sys.exit(1)
    else:
        print(f"✅ All {len(skill_files)} skills passed validation")


if __name__ == "__main__":
    main()
