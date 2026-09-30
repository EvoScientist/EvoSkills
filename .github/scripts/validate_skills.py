#!/usr/bin/env python3
"""Validate SKILL.md frontmatter for all skills in the repository."""

import argparse
import glob
import re
import subprocess
import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = ["name", "description", "allowed-tools", "metadata"]
REQUIRED_METADATA = ["author", "version", "tags"]
EXPERT_FILENAME = "EXPERT.md"
# The WebUI compares versions segment by segment as integers and offers no
# update when a segment is not a number.
VERSION_RE = re.compile(r"\d+(\.\d+)*")


def frontmatter_of(content: str) -> str | None:
    """Return the YAML frontmatter of a SKILL.md text, or None when absent."""
    if not content.startswith("---"):
        return None

    # Find the closing ---
    end = content.index("---", 3)
    return content[3:end].strip()


def extract_frontmatter(filepath: str) -> str | None:
    """Extract YAML frontmatter from a SKILL.md file."""
    with open(filepath, encoding="utf-8") as f:
        return frontmatter_of(f.read())


def declares_expert(meta: dict) -> bool:
    declared = meta.get("type")
    if isinstance(declared, str):
        declared = [declared]
    if not isinstance(declared, list):
        return False
    return "expert" in [str(item).strip().lower() for item in declared]


def validate_skill(filepath: str) -> list[str]:
    """Validate a single SKILL.md file. Returns list of error messages."""
    errors = []
    skill_dir = Path(filepath).parent
    skill_name = skill_dir.name

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

    if "name" in data and str(data["name"]) != skill_name:
        errors.append(
            f"{skill_name}: 'name' is {data['name']!r} but must match the directory name"
        )

    # Check metadata sub-fields
    meta = data.get("metadata", {})
    if isinstance(meta, dict):
        for field in REQUIRED_METADATA:
            if field not in meta:
                errors.append(f"{skill_name}: Missing metadata field '{field}'")

        version = meta.get("version")
        if version is not None and not isinstance(version, str):
            # Unquoted, YAML reads 1.10 as the float 1.1.
            errors.append(
                f"{skill_name}: metadata.version {version!r} must be a quoted string such as '1.2.3'"
            )
        elif version is not None and not VERSION_RE.fullmatch(version):
            errors.append(
                f"{skill_name}: metadata.version {version!r} must be dotted numbers such as '1.2.3'"
            )

        # An expert is declared by a sibling EXPERT.md; metadata.type is the
        # projection of that declaration for catalog listings.
        has_expert_md = (skill_dir / EXPERT_FILENAME).is_file()
        if has_expert_md and not declares_expert(meta):
            errors.append(
                f"{skill_name}: has {EXPERT_FILENAME} but metadata.type does not include 'expert'"
            )
        if declares_expert(meta) and not has_expert_md:
            errors.append(
                f"{skill_name}: metadata.type includes 'expert' but there is no {EXPERT_FILENAME}"
            )
    elif "metadata" in data:
        errors.append(f"{skill_name}: 'metadata' must be a mapping")

    return errors


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def version_of(skill_md: str) -> tuple[int, ...] | None:
    """Return metadata.version of a SKILL.md text as integers, or None."""
    try:
        data = yaml.safe_load(frontmatter_of(skill_md) or "")
    except (ValueError, yaml.YAMLError):
        return None
    meta = data.get("metadata") if isinstance(data, dict) else None
    version = str(meta.get("version", "")) if isinstance(meta, dict) else ""
    if not VERSION_RE.fullmatch(version):
        return None
    return tuple(int(part) for part in version.split("."))


def is_newer(current: tuple[int, ...], base: tuple[int, ...]) -> bool:
    width = max(len(current), len(base))
    padded_current = current + (0,) * (width - len(current))
    padded_base = base + (0,) * (width - len(base))
    return padded_current > padded_base


def check_version_bumps(base_ref: str) -> list[str]:
    """Every skill with files changed since the merge base must raise its version."""
    merge_base = git("merge-base", base_ref, "HEAD")
    if merge_base.returncode != 0:
        return [
            f"cannot find a merge base with {base_ref!r}: {merge_base.stderr.strip()}"
        ]
    base = merge_base.stdout.strip()

    # -z: NUL-separated and unquoted, so unusual path names survive intact.
    changed = git("diff", "--name-only", "-z", base, "--", "skills").stdout.split("\0")
    changed += git(
        "ls-files", "--others", "--exclude-standard", "-z", "--", "skills"
    ).stdout.split("\0")
    # skills/<name>/<file...>; files directly under skills/ belong to no skill.
    names = sorted({Path(p).parts[1] for p in changed if len(Path(p).parts) > 2})

    errors = []
    for name in names:
        skill_md = Path("skills") / name / "SKILL.md"
        at_base = git("show", f"{base}:skills/{name}/SKILL.md")
        if not skill_md.is_file() or at_base.returncode != 0:
            continue  # removed or new skill
        current = version_of(skill_md.read_text(encoding="utf-8"))
        previous = version_of(at_base.stdout)
        if current is None or previous is None:
            continue  # reported by validate_skill, or nothing to compare against
        if not is_newer(current, previous):
            errors.append(
                f"{name}: files changed but metadata.version is "
                f"{'.'.join(map(str, current))} (base has {'.'.join(map(str, previous))}) "
                "— bump metadata.version"
            )
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        metavar="REF",
        help="also require every skill changed since the merge base with REF "
        "to have a higher metadata.version (e.g. --base origin/main)",
    )
    args = parser.parse_args()

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

    if args.base:
        bump_errors = check_version_bumps(args.base)
        for e in bump_errors:
            print(f"  ❌ {e}")
        all_errors.extend(bump_errors)

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
