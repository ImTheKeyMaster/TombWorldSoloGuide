from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


SOLO_HEADER = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
SOLO_PROMPT = section("function runNpoPrompt", "function chooseNpoDecision")
HUMAN_SHELL = section("function renderHumanActivationShell", "function renderHumanPlayerActionPicker")
HUMAN_NPO_PICKER = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")


def test_solo_header_omits_standalone_apl_and_order_pills():
    assert "<span>APL " not in SOLO_HEADER
    assert "<span>Order:" not in SOLO_HEADER
    assert "Order: Conceal" not in SOLO_HEADER
    assert "Order: Engage" not in SOLO_HEADER


def test_solo_header_preserves_wounds_ap_loadout_and_effects():
    assert "<span>Wounds: ${n.wounds}/${n.maxWounds}</span>" in SOLO_HEADER
    assert "<span>AP remaining: ${state.lastActivation.remainingAp}/${state.lastActivation.startingAp}</span>" in SOLO_HEADER
    assert "${loadout?`<span>${escapeHtml(loadout)}</span>`:''}" in SOLO_HEADER
    assert "${modifiers.map(item=>`<span>" in SOLO_HEADER
    assert "Next movement uses Molecular Breach" in SOLO_HEADER
    assert "STAGE3_RULE_TEXT.engrammatic" in SOLO_HEADER
    assert 'role="status" aria-live="polite" aria-label="Activation profile"' in SOLO_HEADER


def test_apl_ap_and_order_game_state_are_unchanged():
    effective_apl = section("function effectiveApl", "function effectiveWeaponProfile")
    activation = section("function beginNpoActivation", "function beginPlayerActivation")
    legality = section("function filterLegalNpoActions", "function rankLegalNpoActions")
    assert "definition.apl" in activation
    assert "effectiveApl(n.id,definition.apl)" in activation
    assert "startingAp:apl,remainingAp:apl" in activation
    assert "activation.remainingAp" in APP
    assert "effectiveNpoApl" in effective_apl
    assert "aplModifiers" in APP
    assert "ordersExcluded" in legality
    assert "n.order" in APP
    assert "orderRule" in APP


def test_solo_ai_guidance_controls_and_navigation_are_unchanged():
    inquiries = section("const NPO_ACTION_INQUIRIES=", "function npoMovementFocus")
    decisions = section("function chooseNpoDecision", "function continueNpoActivation")
    movement = section("function npoMovementInquiry", "function npoMovementInstruction")
    assert "Is this NPO within the control range of any Player operative?" in inquiries
    assert 'data-answer="no"' in APP and 'data-answer="yes"' in APP
    assert "Shoot" in decisions
    assert "Fight" in decisions
    assert "Reposition" in movement
    assert "Dash" in movement
    assert '>Back</button>' in APP
    assert '>Close Guide</button>' in APP


def test_every_solo_npo_uses_the_shared_header_path():
    for npo_type in (
        "Necron Warrior", "Canoptek Macrocyte Warrior", "Canoptek Scarab Swarm",
        "Flayed One", "Skorpekh Destroyer", "Hexmark Destroyer",
        "Royal Warden", "Lychguard",
    ):
        assert f"'{npo_type}':" in APP
    assert "${renderNpoActivationHeader(n)}" in SOLO_PROMPT
    movement = section("function renderNpoMovementConfirmation", "function renderNpoDecisionResult")
    assert "${renderNpoActivationHeader(n)}" in movement
    assert APP.count("function renderNpoActivationHeader(n)") == 1


def test_human_player_and_pvp_necron_headers_remain_clean():
    assert "<span>APL " not in HUMAN_SHELL
    assert "<span>Order:" not in HUMAN_SHELL
    assert "<span>Wounds: ${wounds}/${maxWounds}</span>" in HUMAN_SHELL
    assert "${remainingAp} / ${startingAp} AP remaining" in HUMAN_SHELL
    assert "renderHumanActivationShell({" in HUMAN_NPO_PICKER
    assert "order:n.order" in HUMAN_NPO_PICKER


def test_apl_and_order_remain_available_on_other_surfaces_and_in_logic():
    datacard = section("function npoRosterCard", "function operativeCard")
    assert "APL" in datacard
    assert "Order" in APP
    assert "target.order==='Conceal'" in APP
    assert "item.order==='Engage'" in APP


def test_release_surfaces_and_persistence_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 17)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
