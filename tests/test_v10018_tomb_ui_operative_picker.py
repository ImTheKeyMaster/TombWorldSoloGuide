from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "tomb-ui-v2.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_surfaces_are_synchronized():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")


def test_tomb_picker_is_feature_flagged_and_classic_picker_remains():
    selection = section("function showPlayerActivation()", "function playerActivationSummary")
    assert "document.documentElement.dataset.ui==='tomb'" in selection
    assert "showTombPlayerOperativeSelection(candidates)" in selection
    assert '<select id="humanPlayerSelection"' in selection
    assert "beginPlayerActivation($('#humanPlayerSelection').value)" in selection


def test_tomb_selection_preserves_accessibility_and_activation_path():
    picker = section("const TOMB_V2_ASSET_ROOT", "function showPlayerActivation()")
    collection = "$$('[data-tomb-player-operative]',modal)"
    assert picker.count(collection) == 2
    assert 'role="radiogroup"' in picker
    assert 'role="radio"' in picker
    assert "card.classList.toggle('selected',selected)" in picker
    assert "card.setAttribute('aria-checked',String(selected))" in picker
    assert "status.textContent=selected?'SELECTED':'READY'" in picker
    assert "confirm.disabled=false" in picker
    assert "beginPlayerActivation(selectedId)" in picker


def test_tomb_styles_stay_scoped_and_assets_are_precached():
    for selector in (".tomb-v2-shell", ".tomb-v2-card", ".tomb-v2-operative-grid", ".tomb-v2-radio"):
        assert f'html[data-ui="tomb"] {selector}' in CSS
    assert "./tomb-ui-v2.css" in WORKER
    assert "./Assets/Images/TombUI/v2/portrait-sprite.webp" in WORKER


def test_save_schema_is_unchanged():
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
