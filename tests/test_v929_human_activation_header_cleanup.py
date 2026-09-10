from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


SHELL = section("function renderHumanActivationShell", "function renderHumanPlayerActionPicker")
PLAYER_PICKER = section("function renderHumanPlayerActionPicker", "function playerSequentialStage")
NPO_PICKER = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")


def test_shared_header_omits_standalone_apl_and_every_order_value():
    assert "<span>APL ${baseApl}" not in SHELL
    assert "<span>Order:" not in SHELL
    for value in ("Tabletop", "Engage", "Conceal"):
        assert f"Order: {value}" not in SHELL


def test_shared_header_preserves_wounds_ap_loadout_and_effect_pills():
    assert "<span>Wounds: ${wounds}/${maxWounds}</span>" in SHELL
    assert "${remainingAp} / ${startingAp} AP remaining" in SHELL
    assert "${loadout?`<span>${escapeHtml(loadout)}</span>`:''}" in SHELL
    assert "${effects.map(effect=>`<span>${escapeHtml(effect)}</span>`).join('')}" in SHELL


def test_player_activation_preserves_apl_ap_and_order_state_inputs():
    initialization = section("function beginPlayerActivation", "function playerHumanActionCatalog")
    assert "baseApl,effectiveApl:apl,startingAp:apl,remainingAp:apl" in initialization
    assert "baseApl:activation.baseApl" in PLAYER_PICKER
    assert "effectiveAp:activation.effectiveApl" in PLAYER_PICKER
    assert "remainingAp:activation.remainingAp" in PLAYER_PICKER
    assert "startingAp:activation.startingAp" in PLAYER_PICKER
    assert "order:state.playerOperativeStates?.[activation.operativeId]?.order||'Tabletop'" in PLAYER_PICKER


def test_player_and_pvp_necron_use_the_same_cleaned_shell():
    assert "renderHumanActivationShell({" in PLAYER_PICKER
    assert "renderHumanActivationShell({" in NPO_PICKER
    assert "baseApl:definition.apl" in NPO_PICKER
    assert "effectiveAp:activation.effectiveApl" in NPO_PICKER
    assert "order:n.order" in NPO_PICKER


def test_completed_actions_and_action_groups_are_unchanged():
    assert "HUMAN_ACTION_GROUPS.map" in SHELL
    assert "Completed Actions" in SHELL
    assert 'class="activation-groups"' in SHELL
    assert 'data-human-action="${escapeHtml(action.id)}"' in SHELL


def test_apl_modifiers_and_order_legality_remain_in_gameplay_logic():
    assert "function applyStunForAttack" in APP
    assert "ruleId:'stun',amount:-1" in APP
    assert "function resolveHorrifyingFlaying" in APP
    assert "applyTemporaryAplModifier" in APP
    assert "ordersExcluded?.includes(n.order)" in APP
    assert "target.order==='Conceal'" in APP
    assert "item.order==='Engage'" in APP


def test_existing_mobile_wrapping_and_accessible_status_region_remain():
    assert 'role="status" aria-label="Activation profile"' in SHELL
    assert ".human-activation-shell .activation-profile-strip{display:flex;flex-wrap:wrap" in CSS
    assert ".human-activation-shell .activation-profile-strip span{min-width:0;max-width:100%;overflow-wrap:anywhere}" in CSS


def test_release_surfaces_and_save_contract_are_current():
    version = CURRENT_APP_VERSION
    assert f"const APP_VERSION = '{version}';" in APP
    assert f"const APP_VERSION = '{version}';" in WORKER
    assert f'<div class="version">V{version}</div>' in INDEX
    assert INDEX.count(f"?v={version}") == 10
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{version}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
