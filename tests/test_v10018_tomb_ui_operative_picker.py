import re
import subprocess
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
    assert CURRENT_APP_VERSION == "10.0.18"
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


def test_tomb_picker_enumerates_every_card_and_preserves_activation_path():
    picker = section("function showTombPlayerOperativeSelection", "function showPlayerActivation()")
    collection = "$$('[data-tomb-player-operative]',modal)"
    assert picker.count(collection) == 2
    assert not re.search(r"(?<!\$)\$\('\[data-tomb-player-operative\]'\s*,\s*modal\)\.forEach", picker)
    assert re.search(
        rf"{re.escape(collection)}\.forEach\(button=>button\.onclick=\(\)=>\{{"
        r".*?selectedId=button\.dataset\.tombPlayerOperative;"
        rf".*?{re.escape(collection)}\.forEach\(card=>\{{"
        r".*?card\.dataset\.tombPlayerOperative===selectedId;",
        picker,
        re.DOTALL,
    )
    assert "beginPlayerActivation(selectedId)" in picker
    begin = section("function beginPlayerActivation", "function playerHumanActionCatalog")
    assert "remainingPlayerOperatives().includes(operativeId)" in begin


def test_tomb_picker_runtime_selects_switches_and_continues_exact_card():
    picker_source = "function showTombPlayerOperativeSelection" + section(
        "function showTombPlayerOperativeSelection", "function showPlayerActivation()"
    )
    script = f"""
const cards = ['alpha', 'bravo', 'charlie'].map(id => ({{
  dataset: {{tombPlayerOperative: id}},
  attributes: {{'aria-checked': 'false'}},
  selected: false,
  frame: {{src: ''}},
  state: {{textContent: 'READY'}},
  classList: {{toggle(name, value) {{ if (name === 'selected') this.owner.selected = value; }}}},
  setAttribute(name, value) {{ this.attributes[name] = value; }}
}}));
cards.forEach(card => card.classList.owner = card);
const confirm = {{disabled: true, onclick: null}};
const modal = {{classList: {{add() {{}}}}}};
let modalContent = '';
let activated = null;
const $ = (selector, root) => selector === '#confirmTombPlayerSelection' ? confirm
  : selector === '.tomb-operative-frame' ? root.frame
  : selector === '.tomb-operative-state' ? root.state
  : selector === '[data-tomb-player-operative]' ? cards[0] : null;
const $$ = selector => selector === '[data-tomb-player-operative]' ? cards : [];
const showModal = (title, content) => {{ modalContent = content; }};
const beginPlayerActivation = id => {{ activated = id; }};
const livePlayerOperative = id => ({{role: 'Trooper', apl: 2, wounds: 8}});
const playerDefinition = id => ({{role: 'Trooper', apl: 2, wounds: 8}});
const playerCurrentWounds = id => 8;
const playerName = id => id;
const selectedPlayerTeamName = () => 'Test Team';
const escapeHtml = value => String(value);
{picker_source}
showTombPlayerOperativeSelection(['alpha', 'bravo', 'charlie']);
if (!modalContent.includes('data-close')) throw new Error('Close Guide path missing');
if (!confirm.disabled || cards.some(card => card.selected)) throw new Error('focus implicitly selected a card');
cards[1].onclick();
if (confirm.disabled || !cards[1].selected || cards[0].selected || cards[2].selected) throw new Error('exact card was not selected');
if (cards[1].attributes['aria-checked'] !== 'true' || cards[0].attributes['aria-checked'] !== 'false') throw new Error('aria state mismatch');
if (!cards[1].frame.src.endsWith('operative-selected.webp') || cards[1].state.textContent !== 'SELECTED') throw new Error('selected assets mismatch');
cards[0].onclick();
if (!cards[0].selected || cards[1].selected || !cards[1].frame.src.endsWith('operative-ready.webp') || cards[1].state.textContent !== 'READY') throw new Error('selection did not switch');
confirm.onclick();
if (activated !== 'alpha') throw new Error(`wrong activation: ${{activated}}`);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_tomb_picker_selection_state_switches_without_implicit_focus_selection():
    picker = section("function showTombPlayerOperativeSelection", "function showPlayerActivation()")
    assert 'role="radio" aria-checked="false"' in picker
    assert "index===0?'data-dialog-focus':''" in picker
    assert 'class="tomb-operative-card selected"' not in picker
    assert "let selectedId=''" in picker
    assert "card.classList.toggle('selected',selected)" in picker
    assert "card.setAttribute('aria-checked',String(selected))" in picker
    assert "frame.src=selected?selectedFrame:readyFrame" in picker
    assert "stateLabel.textContent=selected?'SELECTED':'READY'" in picker
    assert "confirm.disabled=false" in picker


def test_tomb_picker_styles_are_scoped_to_experimental_ui():
    assert 'html[data-ui="tomb"] .tomb-operative-picker-shell' in CSS
    assert 'html[data-ui="tomb"] .tomb-operative-card' in CSS
    assert 'html[data-ui="tomb"] .tomb-graphic-button' in CSS
    assert 'Assets/Images/TombUI/tomb-background.webp' in CSS
    picker_css = CSS.split('/* v10.0.18: experimental Tomb UI operative picker.', 1)[1]
    tomb_selector_lines = [line.strip() for line in picker_css.splitlines() if '.tomb-' in line and line.rstrip().endswith('{')]
    assert tomb_selector_lines
    assert all(line.startswith('html[data-ui="tomb"]') for line in tomb_selector_lines)


def test_tomb_picker_has_deliberate_visual_zones_and_small_height_landscape_layout():
    picker = section("function showTombPlayerOperativeSelection", "function showPlayerActivation()")
    for zone in (
        "tomb-picker-intro",
        "tomb-operative-portrait-slot",
        "tomb-operative-copy",
        "tomb-operative-stats",
    ):
        assert zone in picker
    assert "aspect-ratio:3/1" in CSS
    assert 'html[data-ui="tomb"] .tomb-operative-frame' in CSS
    landscape = CSS.split('@media(orientation:landscape) and (max-height:500px)', 1)[1]
    assert 'html[data-ui="tomb"] .modal.tomb-operative-picker-modal' in landscape
    assert 'env(safe-area-inset-top)' in landscape
    assert 'grid-template-columns:minmax(150px,.65fr) minmax(0,1.8fr)' in landscape
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in landscape
    assert 'overflow-y:auto' in landscape
    assert 'html[data-ui="tomb"] .tomb-picker-actions' in landscape


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
