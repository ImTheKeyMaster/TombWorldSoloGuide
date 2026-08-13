"""Shared access to the canonical application release version for tests."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VERSION_DECLARATION = re.compile(
    r"^\s*const\s+APP_VERSION\s*=\s*(['\"])(?P<version>[^'\"]+)\1\s*;\s*$",
    re.MULTILINE,
)
SEMANTIC_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def read_app_version(app_path=ROOT / "app.js"):
    """Return app.js's single, well-formed APP_VERSION declaration."""
    declarations = [match.group("version") for match in APP_VERSION_DECLARATION.finditer(app_path.read_text())]
    if len(declarations) != 1:
        raise RuntimeError(
            f"Expected exactly one APP_VERSION declaration in {app_path}; found {len(declarations)}."
        )
    version = declarations[0]
    if not SEMANTIC_VERSION.fullmatch(version):
        raise RuntimeError(f"Malformed APP_VERSION {version!r} in {app_path}; expected X.Y.Z.")
    return version


CURRENT_APP_VERSION = read_app_version()
