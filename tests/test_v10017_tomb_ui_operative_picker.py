from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_surfaces_are_synchronized():
    assert CURRENT_APP_VERSION == "10.0.17"
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


def test_tomb_picker_uses_graphical_assets_and_live_html():
    picker = section("function showTombPlayerOperativeSelection", "function showPlayerActivation()")
    for asset in (
        "Assets/Images/TombUI/operative-ready.webp",
        "Assets/Images/TombUI/operative-selected.webp",
        "Assets/Images/TombUI/tomb-header.webp",
        "Assets/Images/TombUI/button-primary.webp",
        "Assets/Images/TombUI/button-secondary.webp",
    ):
        assert asset in picker
    assert "playerName(id)" in picker
    assert "operative.role" in picker
    assert "playerCurrentWounds(id)" in picker
    assert "role=\"radiogroup\"" in picker
    assert "role=\"radio\"" in picker
    assert "aria-checked" in picker


def test_tomb_picker_selection_does_not_change_activation_logic():
    picker = section("function showTombPlayerOperativeSelection", "function showPlayerActivation()")
    assert "beginPlayerActivation(selectedId)" in picker
    begin = section("function beginPlayerActivation", "function playerHumanActionCatalog")
    assert "remainingPlayerOperatives().includes(operativeId)" in begin


def test_tomb_picker_styles_are_scoped_to_experimental_ui():
    assert 'html[data-ui="tomb"] .tomb-operative-picker-shell' in CSS
    assert 'html[data-ui="tomb"] .tomb-operative-card' in CSS
    assert 'html[data-ui="tomb"] .tomb-graphic-button' in CSS
    assert 'Assets/Images/TombUI/tomb-background.webp' in CSS


def test_tomb_assets_are_precached_for_pwa_use():
    for asset in (
        "./Assets/Images/TombUI/tomb-background.webp",
        "./Assets/Images/TombUI/tomb-header.webp",
        "./Assets/Images/TombUI/operative-ready.webp",
        "./Assets/Images/TombUI/operative-selected.webp",
        "./Assets/Images/TombUI/button-primary.webp",
        "./Assets/Images/TombUI/button-secondary.webp",
    ):
        assert asset in WORKER


def test_save_schema_is_unchanged():
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
