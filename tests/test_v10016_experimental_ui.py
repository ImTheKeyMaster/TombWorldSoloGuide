"""Regression coverage for the former experimental UI, now the standard experience."""

from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_release_version_is_consistent():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 127)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP


def test_tomb_ui_is_the_default_before_css_and_when_storage_fails():
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
    assert "document.documentElement.dataset.ui = 'classic'" not in INDEX
    assert "document.documentElement.dataset.ui='classic'" not in APP
    assert "tombWorldSolo.experimentalUI.v1" not in INDEX
    assert "tombWorldSolo.experimentalUI.v1" not in APP
    assert INDEX.index('data-ui="tomb"') < INDEX.index('href="styles.css')
    assert "html[data-ui=\"tomb\"] .setup-true-hex-card" in CSS


def test_experimental_playground_is_separate_from_standard_ui():
    key = "tombWorldSolo.experimentalFeatures.v1"
    assert key in INDEX
    assert f"const EXPERIMENTAL_FEATURES_KEY = '{key}';" in APP
    assert INDEX.index(key) < INDEX.index('href="styles.css')
    assert "document.documentElement.dataset.experimental = 'on';" in INDEX
    assert "function experimentalFeaturesEnabled()" in APP
    setter = APP[APP.index("function setExperimentalFeatures") : APP.index("function showExperimentalUiPanel")]
    assert "document.documentElement.dataset.experimental=enabled?'on':'off';" in setter
    assert "localStorage.setItem(EXPERIMENTAL_FEATURES_KEY,'on');" in setter
    assert "localStorage.removeItem(EXPERIMENTAL_FEATURES_KEY);" in setter
    assert "dataset.ui=" not in setter
    assert "experimentalUiToggle.checked=experimentalFeaturesEnabled();" in APP
    assert "Experimental Features" in INDEX
    assert "The approved green Deathwatch portraits are now standard" in INDEX


def test_hidden_version_tap_access_still_works_and_saves_are_unaffected():
    assert "if(versionTapTimes.length<7)return;" in APP
    assert "now-timestamp<=5000" in APP
    assert "document.addEventListener('pointerup'" in APP
    assert 'aria-modal="true" aria-labelledby="experimentalUiTitle"' in INDEX
    assert 'id="experimentalUiToggle" type="checkbox" role="switch"' in INDEX
    assert "experimentalUiToggle.addEventListener('change',()=>setExperimentalFeatures(experimentalUiToggle.checked));" in APP
    save_function = APP[APP.index("function save()") : APP.index("function migrateSupportedSave")]
    assert "EXPERIMENTAL_FEATURES_KEY" not in save_function
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
