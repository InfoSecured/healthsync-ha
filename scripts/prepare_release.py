#!/usr/bin/env python3
"""Prepare a release: bump manifest version and roll Unreleased into a release section."""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
MANIFEST = ROOT / "custom_components" / "apple_healthkit" / "manifest.json"


def update_manifest(version: str) -> None:
    if not MANIFEST.exists():
        raise SystemExit("manifest.json not found")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["version"] = version
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def update_changelog(version: str) -> None:
    if not CHANGELOG.exists():
        raise SystemExit("CHANGELOG.md not found")

    content = CHANGELOG.read_text(encoding="utf-8")
    pattern = r"## \[Unreleased\](.*?)(?=## \[|$)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise SystemExit("No [Unreleased] section found in CHANGELOG.md")

    unreleased_body = match.group(1).strip()
    date = _dt.date.today().isoformat()

    if not unreleased_body:
        unreleased_body = "### Added\n- Pending\n\n### Changed\n- Pending\n\n### Fixed\n- Pending"

    new_unreleased = "## [Unreleased]\n### Added\n- Pending\n\n### Changed\n- Pending\n\n### Fixed\n- Pending"
    new_version_section = f"## [{version}] - {date}\n{unreleased_body}"

    replacement = f"{new_unreleased}\n\n{new_version_section}\n"
    updated = content.replace(match.group(0), replacement, 1)
    CHANGELOG.write_text(updated, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: prepare_release.py <version>")
    version = sys.argv[1].strip()
    if not version:
        raise SystemExit("Version is required")

    update_manifest(version)
    update_changelog(version)


if __name__ == "__main__":
    main()
