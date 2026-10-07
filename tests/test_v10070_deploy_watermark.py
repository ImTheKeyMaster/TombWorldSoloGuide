from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
WATERMARK = (ROOT / "Assets/Images/deploy-watermark.svg").read_text(encoding="utf-8")


def test_release_surfaces_are_v10070_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 70)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_watermark_hook_is_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-watermark-card':''" in render_setup
    assert render_setup.count("deploy-watermark-card") == 1


def test_watermark_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-watermark-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-watermark-card' not in CSS
    before = CSS.split(f"{scope}::before{{", 1)[1].split("}", 1)[0]
    assert 'background-image:url("Assets/Images/deploy-watermark.svg")' in before
    assert "pointer-events:none" in before
    assert "opacity:.055" in before
    assert "z-index:0" in before
    assert f"{scope}>*" in CSS
    card = CSS.split(f"{scope}{{", 1)[1].split("}", 1)[0]
    assert "overflow:hidden" not in card


def test_watermark_asset_is_precached_and_originally_named():
    assert "'./Assets/Images/deploy-watermark.svg'" in WORKER
    assert "weathered skull" in WATERMARK
    assert "segmented mechanical halo" in WATERMARK
    assert "faction" not in WATERMARK.lower()
    assert "<image" not in WATERMARK
    assert "<script" not in WATERMARK.lower()


def test_watermark_does_not_restyle_controls_or_checklist():
    block = CSS.split("experimental-only grim-dark watermark", 1)[1]
    assert ".btn" not in block
    assert ".check-row" not in block
    assert ".deployment-item" not in block
    assert ".wizard-actions" not in block
