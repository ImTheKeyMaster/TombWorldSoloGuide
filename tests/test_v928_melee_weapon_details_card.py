from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
EXPECTED_VERSION = CURRENT_APP_VERSION


def wizard_source():
    start = APP.index("function showPendingPlayerAttackWizard")
    return APP[start:APP.index("function showPlayerCombatResolution", start)]


WIZARD = wizard_source()


def test_melee_dropdown_remains_the_only_selected_weapon_name_display():
    assert '<label>Weapon</label><select id="playerWeaponSelect">' in WIZARD
    assert '<option value="">Select a weapon...</option>' in WIZARD
    melee_render = WIZARD[WIZARD.index("$('#playerWeaponSummaryContent').innerHTML"):]
    melee_branch = melee_render.split(": (weapon?", 1)[0]
    assert "escapeHtml(weapon.name)" not in melee_branch
    assert "${weapon.attacks} dice · ${weapon.hit}+ · ${escapeHtml(weapon.damage)}" in melee_branch


def test_stats_and_rules_share_one_melee_details_card():
    assert "melee-weapon-details melee-weapon-summary-pending" in WIZARD
    assert "weaponRulesHtml(profile,{semanticHeading:true})" in WIZARD
    assert "semanticHeading?'<h3>Weapon Rules</h3>'" in APP
    assert "${attackType==='shoot'?'<div id=\"weaponRules\"></div>':''}" in WIZARD
    assert ".melee-weapon-details .weapon-rules" in CSS
    nested_style = CSS[CSS.index(".melee-weapon-details .weapon-rules{"):].split("}", 1)[0]
    assert "border:0" in nested_style
    assert "border-top:1px solid var(--line)" in nested_style
    assert "background:transparent" in nested_style


def test_rules_heading_is_omitted_when_profile_has_no_rules():
    helper = APP[APP.index("function weaponRulesHtml"):APP.index("function normalizedGuidanceMatchText")]
    assert "return summaries?" in helper
    assert ":'';" in helper
    assert "<h3>Weapon Rules</h3>" in helper


def test_rule_summaries_and_support_statuses_are_unchanged():
    assert "if(handler.mode==='automatic')return {id,label:`${rule}: Handled automatically.`}" in APP
    assert "label:`${rule} is not yet supported by the Guide.`" in APP
    deathwatch = (ROOT / "Player_Operatives" / "DeathWatch.json").read_text(encoding="utf-8")
    assert '"Lethal 5+"' in deathwatch
    assert '"Brutal"' in deathwatch
    assert '"Phase Sweep"' in deathwatch


def test_preselection_card_stays_hidden_visually_and_accessibly_with_reserved_space():
    assert "melee-weapon-summary-pending':''" in WIZARD
    assert "attackType==='melee'?' aria-hidden=\"true\"':''" in WIZARD
    assert "weaponSummary.classList.toggle('melee-weapon-summary-pending',!weapon)" in WIZARD
    assert "weaponSummary.setAttribute('aria-hidden',String(!weapon))" in WIZARD
    assert "${attackType==='melee'?'':'<strong>Weapon:</strong> —'}" in WIZARD
    assert ".melee-weapon-summary-sizer,.melee-weapon-summary-pending{visibility:hidden}" in CSS
    assert ".melee-weapon-summary-pending{display:none}" not in CSS


def test_validation_macrocyte_and_shoot_paths_are_preserved():
    assert "$('#openCombatResolution').disabled=!target||!weapon;" in WIZARD
    assert "$('#aggressiveDefenseFields').innerHTML=aggressiveDefenseFields(target);" in WIZARD
    assert '<strong>Attacker is within 2&quot; of this Macrocyte</strong>' in APP
    shoot_branch = WIZARD[WIZARD.index(": (weapon?`<strong>Weapon:</strong>"):]
    assert "escapeHtml(weapon.name)" in shoot_branch
    assert "if(weaponRules)weaponRules.innerHTML=weaponRulesHtml(profile);" in WIZARD


def test_v928_release_and_save_schema_surfaces():
    assert f"const APP_VERSION = '{EXPECTED_VERSION}';" in APP
    assert f"const APP_VERSION = '{EXPECTED_VERSION}';" in WORKER
    assert "tomb-world-battle-guide-" in WORKER
    assert f"V{EXPECTED_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{EXPECTED_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
