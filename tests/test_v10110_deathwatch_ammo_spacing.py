"""Ensure only Deathwatch's shooting ammunition field gets extra separation."""
from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_deathwatch_ammunition_is_separate_field_after_weapon():
    start = APP.index("    const weaponFieldClass='field weapon-field';")
    end = APP.index("    const secondShoot=", start)
    section = APP[start:end]
    assert "const ammunitionAvailable=attackType==='shoot'&&isDeathwatchPlayerTeam()" in section
    assert 'class="field deathwatch-ammunition-field"' in section
    assert 'for="deathwatchAmmo"' in section
    assert section.index("const weaponControl=") < section.index("const ammunitionControl=")
    assert APP.index("      ${weaponControl}") < APP.index("      ${ammunitionControl}")


def test_spacing_is_scoped_to_adjacent_ammunition_field():
    assert re.search(
        r"\.weapon-field\s*\+\s*\.deathwatch-ammunition-field\s*"
        r"\{\s*margin-top:\s*12px\s*\}", CSS
    )
    assert ".weapon-field{margin-top:6px}" in CSS
    assert CURRENT_APP_VERSION == "10.1.10"
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
