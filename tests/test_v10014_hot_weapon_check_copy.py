import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
HOT = APP[APP.index("const HOT_RULE_EXPLANATION") : APP.index("function createWeaponRuleResolution")]


def test_hot_dialog_copy_is_clear_and_mode_appropriate():
    assert "showModal('HOT WEAPON CHECK'" in HOT
    assert "showModal('HOT'," not in HOT
    assert "This weapon has the Hot rule. After it is used, the Guide checks whether the weapon overheats and injures the attacker." in HOT
    assert "`${isPvpMode()?'Roll':'The Guide rolls'} one D6." in HOT
    assert "title:'HOT WEAPON CHECK'" in HOT
    assert "title:'HOT TEST'" not in HOT
    assert "instruction:`${HOT_RULE_EXPLANATION} ${hotRuleInstruction()}`" in HOT


def test_settled_result_uses_d6_and_effective_hit_terminology():
    assert "D6 Roll: ${record.roll}" in HOT
    assert "Hit Stat: ${record.effectiveHit}+" in HOT
    assert "Hot roll:" not in HOT
    assert "`${record.roll} is lower than ${record.effectiveHit}.`" in HOT
    assert "`${record.roll} is not lower than ${record.effectiveHit}.`" in HOT
    assert 'role="status" aria-live="polite"' in HOT
    assert "ariaLabel:`D6 roll: ${record.roll}`" in HOT


def test_hot_math_and_effective_hit_source_are_unchanged():
    assert "effectiveHit:normalizeEffectiveHit(profile.hit)" in HOT
    assert "const damage=record.roll<record.effectiveHit?record.roll*2:0;" in HOT
    outcomes = {(roll, roll * 2 if roll < 3 else 0) for roll in range(1, 5)}
    assert outcomes == {(1, 2), (2, 4), (3, 0), (4, 0)}


def test_dice_ownership_and_single_roll_path_are_unchanged():
    provider = APP[APP.index("async function requestDiceResults") : APP.index("function pendingDiceContextIsCurrent")]
    resolver = HOT[HOT.index("async function resolveHotTransaction") : HOT.index("async function showHotResult")]
    presentation = HOT[HOT.index("async function showHotResult") : HOT.index("function completeShootingWeaponUse")]
    assert "if(!isPvpMode())return rollDice(validatedRequest.count,validatedRequest.sides);" in provider
    assert "return requestManualDiceResults(validatedRequest);" in provider
    assert resolver.count("requestDiceResults(") == 1
    assert "Math.random" not in resolver + presentation
    assert "TombWorldDiceSfx.play()" not in resolver
    assert presentation.count("TombWorldDiceSfx.play()") == 1


def test_hot_transaction_paths_and_timing_remain_protected():
    assert "if(record.applied)return record" in HOT
    assert "entry.transactionId===record.id" in HOT
    assert "record.attackerSide==='player'" in HOT
    assert "attacker.battlefieldState='out-of-action'" in HOT
    assert "if(record.acknowledged)return record" in HOT
    assert "finishWeaponUse" in APP
    assert "showMultiTargetAttackSummary(completed" in APP
    assert "normalizeHotResolution(raw.hotResolution)" in APP


def test_release_surfaces_and_save_contract():
    assert CURRENT_APP_VERSION == "10.0.14"
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 11
    assert f"analytics.js?release={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert not re.search(r"(?:\?v=|release=|APP_VERSION = ['\"]|<div class=\"version\">V)10\.0\.13", APP + INDEX + WORKER)
