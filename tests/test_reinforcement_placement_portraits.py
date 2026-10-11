from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
INDEX=(ROOT/'index.html').read_text(encoding='utf-8')
WORKER=(ROOT/'service-worker.js').read_text(encoding='utf-8')
PORTRAIT=APP.split('function reinforcementPlacementPortrait(npo)',1)[1].split('function strategyReviewStepHtml(d)',1)[0]
REVIEW=APP.split('function strategyReviewStepHtml(d)',1)[1].split('function reinforcementBlockedReason(',1)[0]

def test_version_consistency():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in INDEX

def test_reinforcements_use_existing_operatives_and_artwork():
    assert "document.documentElement.dataset.ui!=='tomb'" in PORTRAIT
    assert 'experimentalNecronPortraitSvg(npo,' in PORTRAIT
    assert 'reinforcement-placement-artwork' in PORTRAIT
    assert 'aria-hidden="true"' in PORTRAIT
    assert 'const portrait=reinforcementPlacementPortrait(npo)' in REVIEW
    assert "reinforcement-placement-row" in REVIEW
    assert "${portrait}</label>" in REVIEW
    assert 'data-reinforcement-placement=' in REVIEW
    assert "npo.reinforcement?.placementConfirmed?'checked':''" in REVIEW
    assert 'data-reinforcement-replacement=' in REVIEW
    assert 'reinforcement placement restrictions, then confirm.' in REVIEW

def test_art_is_layered_under_the_text_and_checkbox_without_card_height_changes():
    styles=CSS.split('/* Reinforcement placement portraits:',1)[1]
    assert 'position:relative' in styles
    assert 'overflow:hidden' in styles
    assert 'isolation:isolate' in styles
    assert '>input' in styles
    assert '>span:not(.reinforcement-placement-portrait)' in styles
    assert 'position:absolute' in styles
    assert 'top:-20px' in styles and 'right:-12px' in styles
    assert 'transform:scale(1.35)' in styles
    assert 'pointer-events:none' in styles
    assert 'z-index:0' in styles and 'z-index:1' in styles
    assert '@media(max-width:600px)' in styles
