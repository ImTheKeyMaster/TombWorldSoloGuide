from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
CSS = (ROOT / "experimental-cyber.css").read_text()
CLASSIC_CSS = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def test_experimental_cyber_stylesheet_is_versioned_and_cached():
    assert 'experimental-cyber.css?v=10.0.68' in INDEX
    assert './experimental-cyber.css?v=${APP_VERSION}' in WORKER


def test_setup_markup_exposes_step_without_changing_bindings():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert 'class="wizard-shell" data-setup-step="${stepId}"' in render_setup
    assert "bindSetup(stepId);" in render_setup


def test_cyber_deploy_preview_is_strictly_experimental_and_deploy_only():
    scope = 'html[data-ui="tomb"] .wizard-shell[data-setup-step="deploy"]'
    assert scope in CSS
    assert 'html[data-ui="classic"]' not in CSS
    assert '.wizard-shell[data-setup-step="mission"]' not in CSS
    assert '.wizard-shell[data-setup-step="killzone"]' not in CSS
    assert '.wizard-shell[data-setup-step="playerRoster"]' not in CSS
    assert '.wizard-shell[data-setup-step="options"]' not in CSS
    assert '.wizard-shell[data-setup-step="ready"]' not in CSS


def test_preview_changes_outer_dialog_and_actions_but_not_checklist_pills():
    scope = 'html[data-ui="tomb"] .wizard-shell[data-setup-step="deploy"]'
    assert f"{scope} > .wizard-card" in CSS
    card_rule = CSS.split(f"{scope} > .wizard-card{{", 1)[1].split("}", 1)[0]
    before_rule = CSS.split(f"{scope} > .wizard-card::before{{", 1)[1].split("}", 1)[0]
    assert "--cyber-frame-clip:polygon(" in card_rule
    assert "clip-path:" not in card_rule
    assert "\n  filter:" not in card_rule
    assert "\n  animation:" not in card_rule
    assert "--cyber-accent:#7edfe5" in CSS
    assert "clip-path:var(--cyber-frame-clip)" in CSS
    assert "drop-shadow(5px 6px 0 rgba(255,98,71,.13))" in before_rule
    assert f"{scope} .wizard-actions .btn" in CSS
    assert f"{scope} .setup-bulk-row .btn" in CSS
    assert f"{scope} .check-row" not in CSS
    assert f"{scope} .deployment-check" not in CSS
    assert f"{scope} .checklist" not in CSS


def test_clipped_cyber_buttons_use_visible_inset_focus_treatment():
    focus = CSS.split('.wizard-actions .btn:focus-visible,', 1)[1].split("}", 1)[0]
    assert "outline:none" in focus
    assert "inset 0 0 0 2px #effdff" in focus
    assert "outline-offset" not in focus


def test_mobile_preview_preserves_production_fixed_action_clearance():
    mobile = CSS.split("@media(max-width:600px){", 1)[1].split("@media(prefers-reduced-motion:reduce)", 1)[0]
    card = mobile.split('html[data-ui="tomb"] .wizard-shell[data-setup-step="deploy"] > .wizard-card{', 1)[1].split("}", 1)[0]
    assert "padding-top:20px" in card
    assert "padding-right:18px" in card
    assert "padding-left:18px" in card
    assert "padding:" not in card
    assert "padding-bottom:" not in card


def test_classic_stylesheet_has_no_experimental_cyber_rules():
    assert "--cyber-accent" not in CLASSIC_CSS
    assert "tw-cyber-frame-reveal" not in CLASSIC_CSS
