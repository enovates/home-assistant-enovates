#!/usr/bin/env -S uv run --script
"""Checks that the manifest.json's requirements and requirements.txt are matched."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
assert ROOT.is_dir(), "Repo root is not a folder. Script got moved?"

SPLIT_PATTERN = re.compile(r"[>~=<]{1,2}")


def _main() -> bool:
    requirements_file = ROOT / "requirements.txt"
    manifast_file = ROOT / "custom_components" / "enovates" / "manifest.json"

    assert requirements_file.is_file(), "Requirements file not found"
    assert manifast_file.is_file(), "Manifest file not found"

    manifest = {tuple(map(str.strip, SPLIT_PATTERN.split(i, 1))) for i in json.loads(manifast_file.read_text())["requirements"]}
    requirements = {
        tuple(map(str.strip, SPLIT_PATTERN.split(line, 1)))
        for line in map(str.strip, requirements_file.read_text().splitlines())
        if line and not line.startswith("#")
    }

    missing = manifest - requirements

    if not missing:
        print("OK: All manifest dependencies match requirements.txt file entries.")
        return True

    print("ERROR: Some manifest dependencies are missing from requirements.txt or have mismatched versions:")
    print("Packages:", ", ".join(name for name, _ in missing))
    return False


if __name__ == "__main__":
    exit(0 if _main() else 1)
