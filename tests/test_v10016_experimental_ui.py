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
    assert "Currently previews new styling on Deploy Kill Teams only." in INDEX
    assert 'aria-modal="true" aria-labelledby="experimentalUiTitle"' in INDEX
    experimental_marker = CSS.index("experimental-only cyberpunk treatment")
    experimental_block_start = CSS.rfind("/*", 0, experimental_marker)
    assert experimental_block_start >= 0
    assert 'html[data-ui="tomb"]' not in CSS[:experimental_block_start]
    assert 'tomb-ui-v2.css' not in INDEX
    assert 'Assets/Images/TombUI' not in INDEX
    save_function = APP[APP.index("function save()") : APP.index("function migrateSupportedSave")]
    assert "EXPERIMENTAL_UI_KEY" not in save_function
    setter = APP[APP.index("function setExperimentalUi") : APP.index("function showExperimentalUiPanel")]
    assert setter.index("localStorage.setItem") < setter.index("dataset.ui='tomb'")
    assert "dataset.ui='classic'" in setter


def test_experimental_deploy_cyber_style_is_strictly_scoped():
    deploy_renderer = APP[APP.index("app.innerHTML=`<div class=\"wizard-shell\"") : APP.index("bindSetup(stepId);")]
    assert "experimental-deploy-cyber-card" in deploy_renderer
    assert "stepId==='deploy'" in deploy_renderer
    assert 'html[data-ui="tomb"] .experimental-deploy-cyber-card{' in CSS
    assert '.experimental-deploy-cyber-card{' not in CSS.replace('html[data-ui="tomb"] .experimental-deploy-cyber-card{', '')
    assert "tomb-ui-v2.css" not in INDEX


def test_experimental_deploy_pass_does_not_restyle_checklist_rows():
    experimental_css = CSS.split("experimental-only cyberpunk treatment", 1)[1]
    assert 'html[data-ui="tomb"] .experimental-deploy-cyber-card .check-row' not in experimental_css
    assert 'html[data-ui="tomb"] .experimental-deploy-cyber-card .deployment-check' not in experimental_css


def test_experimental_deploy_preserves_fixed_mobile_action_bar():
    experimental_css = CSS.split("experimental-only cyberpunk treatment", 1)[1]
    card = experimental_css.split('html[data-ui="tomb"] .experimental-deploy-cyber-card{', 1)[1].split("}", 1)[0]
    actions = experimental_css.split('html[data-ui="tomb"] .experimental-deploy-cyber-card>.wizard-actions{', 1)[1].split("}", 1)[0]
    assert "backdrop-filter" not in card
    assert "position:relative" not in actions
    desktop = experimental_css.split("@media(min-width:601px){", 1)[1].split("@keyframes", 1)[0]
    assert 'html[data-ui="tomb"] .experimental-deploy-cyber-card{' in desktop
    assert "backdrop-filter:saturate(150%) blur(7px)" in desktop
    assert "position:relative" in desktop
    mobile = experimental_css.split("@media(max-width:600px){", 1)[1]
    mobile_card = mobile.split('html[data-ui="tomb"] .experimental-deploy-cyber-card{', 1)[1].split("}", 1)[0]
    assert "clip-path:none" in mobile_card
