from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10075_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 75)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_experimental_deploy_returns_to_clean_baseline():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert '<section class="wizard-card"' in render_setup
    assert "deploy-stamps-card" not in render_setup
    assert "deploy-telemetry-card" not in render_setup
    assert "deploy-etched-card" not in render_setup
    assert "deploy-armored-card" not in render_setup
    assert "deploy-stamp-authorized" not in render_setup
    assert "deploy-field-code" not in render_setup


def test_rejected_deploy_visual_experiments_are_absent_from_css():
    rejected = (
        "deploy-stamps-card",
        "deploy-telemetry-card",
        "deploy-etched-card",
        "deploy-armored-card",
        "deploy-corner",
        "experimental-only inspection stamps and field markings",
        "experimental-only deployment telemetry rail",
        "experimental-only etched-metal surface",
    )
    for token in rejected:
        assert token not in CSS


def test_experimental_selector_remains_available():
    assert "Experimental Tomb UI" in INDEX
    assert "Experimental currently mirrors the Current interface." in INDEX
    assert "tombWorldSolo.experimentalUI.v1" in INDEX
