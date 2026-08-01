#!/usr/bin/env python3
"""Generate the landscape background manifest from repository image assets."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND_DIRECTORY = ROOT / "Assets" / "Images" / "Backgrounds"
MANIFEST_PATH = BACKGROUND_DIRECTORY / "manifest.json"
LANDSCAPE_PATTERN = re.compile(r"Landscape-(\d{2,})\.png")


def landscape_filenames(directory: Path) -> list[str]:
    matches = []
    for path in directory.iterdir():
        match = LANDSCAPE_PATTERN.fullmatch(path.name)
        if path.is_file() and match:
            matches.append((int(match.group(1)), path.name))
    return [name for _, name in sorted(matches, key=lambda item: (item[0], item[1]))]


def main() -> None:
    filenames = landscape_filenames(BACKGROUND_DIRECTORY)
    if not filenames:
        raise SystemExit(
            f"No landscape backgrounds matching Landscape-\\d{{2,}}.png found in {BACKGROUND_DIRECTORY}"
        )
    content = json.dumps({"landscape": filenames}, indent=2) + "\n"
    MANIFEST_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH.relative_to(ROOT)} with {len(filenames)} landscape images.")


if __name__ == "__main__":
    main()
