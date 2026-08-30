"""Focused acceptance coverage for persisted Fight outcome feedback."""
from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def body(name):
    match = re.search(rf"  (?:async )?function {re.escape(name)}\([^\n]*\)\{{", APP)
    assert match, name
    depth = 0
    for index in range(APP.find("){", match.start()) + 1, len(APP)):
        if APP[index] == "{":
            depth += 1
        elif APP[index] == "}":
            depth -= 1
            if depth == 0:
                return APP[match.start():index + 1]
    raise AssertionError(name)


def test_result_is_checkpointed_and_acknowledged_before_continuation():
    finish = body("finishFight")
    acknowledge = body("acknowledgeFightResult")
    assert "buildFightResult(fight)" in finish
    assert "fight.resultCommitted=true" in finish
    assert "fight.resultAcknowledged=false" in finish
    assert finish.index("save()") < finish.index("renderFightResult(fight)")
    assert "fight.resultAcknowledged=true;save()" in acknowledge
    assert acknowledge.index("resultAcknowledged=true;save()") < acknowledge.index("continuation(fight.result)")
    assert "state.fightState=null;save()" in acknowledge


def test_result_uses_committed_strikes_and_excludes_blocks():
    damage = body("fightRoleDamage")
    result = body("buildFightResult")
    assert "entry.type==='strike'&&entry.role===role" in damage
    assert "entry.before)-Number(entry.after" in damage
    assert "block" not in damage
    assert "attackerDamageDealt" in result and "defenderDamageDealt" in result
    assert "attackerBefore" in result and "attackerAfter" in result
    assert "defenderBefore" in result and "defenderAfter" in result
    assert "fightTransactionId" in result


def test_playtest_strike_history_totals_three_dealt_and_seven_suffered():
    damage = body("fightRoleDamage")
    script = f"""
{damage}
const history = [
  {{type:'strike',role:'attacker',damage:3,before:7,after:4}},
  {{type:'block',role:'defender',damage:99,before:13,after:13}},
  {{type:'strike',role:'defender',damage:2,before:13,after:11}},
  {{type:'strike',role:'defender',damage:2,before:11,after:9}},
  {{type:'strike',role:'defender',damage:1,before:9,after:8}},
  {{type:'strike',role:'defender',damage:1,before:8,after:7}},
  {{type:'strike',role:'defender',damage:1,before:7,after:6}},
];
if (fightRoleDamage({{history}}, 'attacker') !== 3) process.exit(1);
if (fightRoleDamage({{history}}, 'defender') !== 7) process.exit(2);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_result_screen_summarizes_both_participants_and_continue():
    render = body("renderFightResult")
    card = body("fightResultParticipantHtml")
    assert "Fight Result" in render and "FIGHT FINISHED" in render
    assert "participants.attacker" in render and "participants.defender" in render
    assert "Damage Dealt" in card and "Wounds" in card
    assert "participant.before" in card and "participant.after" in card
    assert "ELIMINATED" in card
    assert "INCAPACITATED" not in card
    assert 'id="continueFightResult"' in render and "data-dialog-focus" in render
    assert "acknowledgeFightResult(fight)" in render


def test_no_success_and_remaining_success_explanations_are_supported():
    explanation = body("fightResultExplanation")
    assert "Neither operative retained a success." in explanation
    assert "No damage was dealt." in explanation
    assert "retained no successes." in explanation
    assert "fight.history.filter" in explanation
    assert "total Strike damage." in explanation


def test_legacy_checkpoint_is_upgraded_without_duplicate_battle_record():
    finish = body("finishFight")
    result = body("buildFightResult")
    assert "resultVersion:2" in result
    assert "completeResult" in finish
    assert "!fight.resultCommitted||!completeResult" in finish
    assert "!fight.resultLogged" in finish
    assert "fight.resultLogged=true" in finish


def test_completed_action_keeps_fight_specific_outcome_fields():
    commit = body("commitHumanPlayerAction")
    npo_summary = body("conciseNpoActionName")
    assert "Dealt ${Number(primary.damageDealt" in commit
    assert "Suffered ${Number(primary.damageSuffered" in commit
    for field in ("damageDealt", "damageSuffered", "attackerBefore", "attackerAfter",
                  "defenderBefore", "defenderAfter", "attackerIncapacitated",
                  "defenderIncapacitated", "fightTransactionId"):
        assert field in commit
    assert "action.id==='fight'" in npo_summary
    assert "fight.targetName" in npo_summary
    assert "fight.damageDealt" in npo_summary
    assert "fight.damageSuffered" in npo_summary
    assert "Dealt" in npo_summary and "Suffered" in npo_summary


def test_solo_pvp_and_engine_decisions_remain_in_existing_resolution_path():
    resolution = body("renderFightResolution")
    assert "participant.side==='player'||isPvpMode()" in resolution
    assert "soloNpoFightDecision" in resolution
    assert "commitFightStrike" in resolution and "commitFightBlock" in resolution
    assert "renderFightResult" not in body("commitFightStrike")
    assert "renderFightResult" not in body("commitFightBlock")


def test_mobile_accessibility_and_release_surfaces():
    expected = CURRENT_APP_VERSION
    assert CURRENT_APP_VERSION == expected
    assert ".fight-result-participants" in CSS
    assert "@media (max-width:374px){.fight-result-participants{grid-template-columns:1fr}" in CSS
    assert "overflow-wrap:anywhere" in CSS
    assert "aria-label=\"Fight finished\"" in body("renderFightResult")
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert all(f"{asset}?v={expected}" in INDEX for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ))
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
