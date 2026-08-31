import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def wizard_source():
    start = APP.index("function showPendingPlayerAttackWizard")
    return APP[start:APP.index("function showPlayerCombatResolution", start)]


WIZARD = wizard_source()


def test_shooting_preserves_weapon_selector_and_readonly_display():
    assert '<label>Weapon</label><select id="playerWeaponSelect">' in WIZARD
    assert '<option value="">Select a weapon...</option>' in WIZARD
    assert '<div class="readonly-select">${escapeHtml(weapons[0].name)}</div>' in WIZARD
    assert '<input type="hidden" id="playerWeaponSelect" value="0">' in WIZARD


def test_selected_name_is_only_rendered_by_weapon_control():
    render = WIZARD[WIZARD.index("const renderChoices=()=>"):]
    assert "escapeHtml(weapon.name)" not in render
    assert "<strong>Weapon:</strong>" not in WIZARD
    assert "Weapon: —" not in WIZARD


def test_stats_and_rules_share_one_details_card():
    assert 'class="summary-box weapon-details${attackType' in WIZARD
    assert '<div class="weapon-profile-stats">${weapon.attacks} dice · ${weapon.hit}+ · ${escapeHtml(weapon.damage)}</div>' in WIZARD
    assert "weaponRulesHtml(profile,{semanticHeading:true})" in WIZARD
    assert 'id="weaponRules"' not in WIZARD
    assert ".weapon-details .weapon-rules" in CSS


def test_rules_heading_and_empty_rules_match_melee():
    helper = APP[APP.index("function weaponRulesHtml"):APP.index("function normalizedGuidanceMatchText")]
    assert "semanticHeading?'<h3>Weapon Rules</h3>'" in helper
    assert "return summaries?" in helper
    assert ":'';" in helper


def test_supported_and_unsupported_rule_wording_is_unchanged():
    assert "if(handler.mode==='automatic')return {id,label:`${rule}: Handled automatically.`}" in APP
    assert "label:`${rule} is not yet supported by the Guide.`" in APP


def test_shooting_no_selection_hides_card_without_melee_reserved_space():
    assert "${attackType==='shoot'?' hidden':''}" in WIZARD
    assert "else weaponSummary.hidden=!weapon;" in WIZARD
    assert "weaponSummary.setAttribute('aria-hidden',String(!weapon))" in WIZARD
    assert "weaponSummary.classList.toggle('melee-weapon-summary-pending',!weapon)" in WIZARD


def test_target_weapon_spacing_and_focus_accessibility_are_shared():
    assert "const weaponFieldClass='field weapon-field';" in WIZARD
    assert ".weapon-field{margin-top:6px}" in CSS
    assert not re.search(r"(?:select|\*):focus(?:-visible)?\s*\{\s*outline\s*:\s*none", CSS)


def test_selection_validation_and_profile_behavior_are_unchanged():
    assert "weaponSelect.value===''?null:weapons[Number(weaponSelect.value)]" in WIZARD
    assert "$('#openCombatResolution').disabled=!target||!weapon;" in WIZARD
    assert "const moreThanEight=Boolean($('#darkOfTombDistance')?.checked);" in WIZARD
    assert "weaponHasRule(profile,'blast')?'blast':weaponHasRule(profile,'torrent')?'torrent':null" in WIZARD
    assert "playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex})" in WIZARD


def test_release_surfaces_and_save_schema():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 12)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
