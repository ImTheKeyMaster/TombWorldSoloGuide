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
EXPECTED_VERSION = CURRENT_APP_VERSION


def attack_wizard_source():
    start = APP.index("function showPendingPlayerAttackWizard")
    end = APP.index("function showPlayerCombatResolution", start)
    return APP[start:end]


WIZARD = attack_wizard_source()


def test_melee_weapon_dropdown_and_reserved_hidden_summary_are_rendered():
    assert '<label>Weapon</label><select id="playerWeaponSelect">' in WIZARD
    assert '<option value="">Select a weapon...</option>' in WIZARD
    assert "attackType==='melee'?' melee-weapon-summary melee-weapon-details melee-weapon-summary-pending':''" in WIZARD
    assert "attackType==='melee'?' aria-hidden=\"true\"':''" in WIZARD
    assert "weapons.map(weapon=>`<div class=\"melee-weapon-summary-sizer\" aria-hidden=\"true\">" in WIZARD
    assert ".melee-weapon-summary{display:grid}" in CSS
    assert ".melee-weapon-summary>div{grid-area:1/1}" in CSS
    assert ".melee-weapon-summary-sizer,.melee-weapon-summary-pending{visibility:hidden}" in CSS
    assert ".melee-weapon-summary-pending{display:none}" not in CSS


def test_weapon_selection_reveals_stats_summary():
    assert "weaponSummary.classList.toggle('melee-weapon-summary-pending',!weapon)" in WIZARD
    assert "weaponSummary.setAttribute('aria-hidden',String(!weapon))" in WIZARD
    assert "$('#playerWeaponSummaryContent').innerHTML=attackType==='melee'" in WIZARD
    assert "${weapon.attacks} dice" in WIZARD
    assert "${weapon.hit}+" in WIZARD
    assert "escapeHtml(weapon.damage)" in WIZARD


def test_continue_validation_is_still_target_and_weapon_based():
    assert "$('#openCombatResolution').disabled=!target||!weapon;" in WIZARD


def test_macrocyte_question_is_unchanged():
    assert '<strong>Attacker is within 2&quot; of this Macrocyte</strong>' in APP
    assert "Required only if this attack incapacitates the Macrocyte." in APP
    assert "$('#aggressiveDefenseFields').innerHTML=aggressiveDefenseFields(target);" in WIZARD


def test_shoot_summary_behavior_is_not_hidden():
    summary_markup = re.search(
        r'<div class="summary-box\$\{attackType.*?id="playerWeaponSummary".*?</div>',
        WIZARD,
    ).group(0)
    assert summary_markup.count("attackType==='melee'") == 3
    assert "attackType==='shoot'" not in summary_markup
    assert "if(attackType==='melee'){" in WIZARD


def test_release_version_surfaces_and_save_schema():
    assert CURRENT_APP_VERSION == EXPECTED_VERSION
    assert f"const APP_VERSION = '{EXPECTED_VERSION}';" in APP
    assert f"const APP_VERSION = '{EXPECTED_VERSION}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert f"V{EXPECTED_VERSION}" in INDEX
    for asset in (
        "styles.css",
        "mission-engine.js",
        "persistence.js",
        "deadly-encounters.js",
        "event-effects.js",
        "audio-capabilities.js",
        "narration.js",
        "ambient.js",
        "dice-sfx.js",
        "app.js",
    ):
        assert f'{asset}?v={EXPECTED_VERSION}' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{EXPECTED_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
