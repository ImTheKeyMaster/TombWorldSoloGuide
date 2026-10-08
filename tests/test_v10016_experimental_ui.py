from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text()
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


def test_release_version_is_consistent():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 16)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP


def test_experimental_ui_defaults_to_classic_and_bootstraps_early():
    assert '<html lang="en" data-ui="classic">' in INDEX
    assert "localStorage.getItem('tombWorldSolo.experimentalUI.v1') === 'tomb'" in INDEX
    assert INDEX.index("tombWorldSolo.experimentalUI.v1") < INDEX.index('href="styles.css')
    assert "document.documentElement.dataset.ui = 'classic'" in INDEX


def test_experimental_ui_is_isolated_and_hidden_behind_version_taps():
    assert "const EXPERIMENTAL_UI_KEY = 'tombWorldSolo.experimentalUI.v1';" in APP
    assert "if(versionTapTimes.length<7)return;" in APP
    assert "now-timestamp<=5000" in APP
    assert "document.addEventListener('pointerup'" in APP
    assert "document.addEventListener('click',event=>" not in APP[APP.index("let versionTapTimes") : APP.index("experimentalUiToggle.addEventListener")]
    assert "Experimental Tomb UI" in INDEX
    assert "Currently previews a subtle etched-metal surface on Deploy Kill Teams." in INDEX
    assert 'aria-modal="true" aria-labelledby="experimentalUiTitle"' in INDEX
    assert 'html[data-ui="tomb"] .deploy-etched-card' in CSS
    assert 'tomb-ui-v2.css' not in INDEX
    assert 'Assets/Images/TombUI' not in INDEX
    save_function = APP[APP.index("function save()") : APP.index("function migrateSupportedSave")]
    assert "EXPERIMENTAL_UI_KEY" not in save_function
    setter = APP[APP.index("function setExperimentalUi") : APP.index("function showExperimentalUiPanel")]
    assert setter.index("localStorage.setItem") < setter.index("dataset.ui='tomb'")
    assert "dataset.ui='classic'" in setter
