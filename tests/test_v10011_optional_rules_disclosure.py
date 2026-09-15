from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")

OPTIONS_RENDER = APP.split("if(stepId==='options'){", 1)[1].split("if(stepId==='deploy'){", 1)[0]
OPTION_BINDINGS = APP.split("function bindSetup(stepId){", 1)[1].split("function runStartingNpoGeneration", 1)[0]


def test_native_disclosure_is_present_and_collapsed_by_default():
    assert '<details class="other-optional-rules" ${optionalRulesExpanded?\'open\':\'\'}>' in OPTIONS_RENDER
    assert "let optionalRulesExpanded=false;" in APP
    assert "if(stepId==='options'&&lastRenderedSetupStepId!=='options')optionalRulesExpanded=false;" in APP


def test_optional_controls_are_inside_disclosure_and_variants_remain_outside():
    details_start = OPTIONS_RENDER.index('<details class="other-optional-rules"')
    details_end = OPTIONS_RENDER.index("</details>", details_start)
    variant_grid = OPTIONS_RENDER.index('<div class="variant-card-grid">')
    restless = OPTIONS_RENDER.index('id="restlessTombEnabled"')
    assert variant_grid < details_start < restless < details_end
    assert OPTIONS_RENDER.index("${deadlyOption}", details_start) < details_end
    assert 'id="deadlyEncountersEnabled"' in OPTIONS_RENDER
    assert 'name="tombWorldVariant"' in OPTIONS_RENDER


def test_native_open_state_controls_visual_visibility_and_accessibility():
    assert "${optionalRulesExpanded?'open':''}" in OPTIONS_RENDER
    assert ".other-optional-rules[open] .optional-rules-chevron" in CSS
    assert ".other-optional-rules summary:focus-visible" in CSS
    assert ".other-optional-rules summary::-webkit-details-marker" in CSS
    assert '<summary><span>Other Optional Rules' in OPTIONS_RENDER


def test_toggle_state_survives_optional_rule_rerenders_without_being_saved():
    assert ".other-optional-rules')?.addEventListener('toggle',e=>{optionalRulesExpanded=e.target.open;});" in OPTION_BINDINGS
    assert "state.restlessTombEnabled=e.target.checked;save();render();" in OPTION_BINDINGS
    assert "state.deadlyEncountersEnabled=e.target.checked;save();render();" in OPTION_BINDINGS
    persisted_state = APP.split("const initialState = () => ({", 1)[1].split("});", 1)[0]
    assert "optionalRulesExpanded" not in persisted_state


def test_collapsing_does_not_mutate_either_optional_rule_selection():
    toggle_handler = OPTION_BINDINGS.split("addEventListener('toggle'", 1)[1].split("});", 1)[0]
    assert "optionalRulesExpanded=e.target.open" in toggle_handler
    assert "restlessTombEnabled" not in toggle_handler
    assert "deadlyEncountersEnabled" not in toggle_handler


def test_continue_and_variant_selection_bindings_are_unchanged():
    assert "$('#setupNext')?.addEventListener('click',()=>advanceSetupStep(stepId));" in OPTION_BINDINGS
    assert "setTombWorldVariant(e.target.value)" in OPTION_BINDINGS
    assert "state.setupStep=Math.min(steps.length-1,state.setupStep+1);save();render();" in APP


def test_checkbox_accessible_names_are_retained():
    assert 'aria-label="Enable Restless Tomb house rule"' in OPTIONS_RENDER
    assert 'aria-label="Enable Deadly Encounters: Tomb Worlds official expansion"' in OPTIONS_RENDER


def test_selected_count_is_quiet_at_zero_and_reports_one_or_two():
    assert "const optionalRuleCount=Number(state.restlessTombEnabled)+Number(!isPvpMode()&&state.deadlyEncountersEnabled);" in OPTIONS_RENDER
    assert "const selectedCount=optionalRuleCount?" in OPTIONS_RENDER
    assert "${optionalRuleCount} selected" in OPTIONS_RENDER
    assert ":'';" in OPTIONS_RENDER


def test_mobile_summary_is_bounded_and_does_not_overflow():
    assert ".other-optional-rules{min-width:0" in CSS
    assert "summary>span:first-child{display:flex;min-width:0" in CSS
    assert "white-space:nowrap" in CSS
    assert "@media(max-width:390px)" in CSS


def test_release_surfaces_and_save_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 11)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 11
    assert f"analytics.js?release={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
