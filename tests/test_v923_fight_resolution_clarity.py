"""Focused acceptance coverage for the Fight resolution clarity release."""
from pathlib import Path
import re

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


def test_fight_roll_keeps_dice_and_gray_failures_without_failure_summary():
    participant = body("fightRollParticipantHtml")
    presentation = body("fightDiePresentation")
    summary = body("fightRollSummary")
    assert "dice.map" in participant and "dieHtml(die)" in participant
    assert "failure" in presentation
    assert ".die.miss" in CSS
    assert "Failure" not in summary
    assert "Critical" in summary and "Normal" in summary
    assert "No retained successes" in summary
    assert APP.count("fightRollSummary(dice)") == 1


def test_actions_are_neutral_grouped_owned_and_accessible():
    render = body("renderFightResolution")
    assert 'btn primary fight-action' not in render
    assert render.count('btn secondary fight-action') == 2
    assert 'id="fightStrikeHeading">STRIKE' in render
    assert "fightBlockHeading" in render
    assert "${escapeHtml(participant.label)}'s Turn" in render
    assert "uses one of its unresolved successes" in render
    assert "aria-label=\"Acting now:" in render
    assert "Strike with ${success.kind} success, deal" in render
    assert "Block enemy ${target.kind} success using" in render
    pool = body("fightPoolHtml")
    assert ".fight-pool.active" in CSS and "ACTING NOW" in pool
    assert "aria-label=\"${active?'Acting now: ':''}${escapeHtml(participant.label)}\"" in pool
    assert "@media (max-width:430px){.fight-actions{grid-template-columns:1fr}" in CSS


def test_equivalent_choices_collapse_to_first_stable_pool_records():
    actions = body("semanticFightActions")
    assert "unresolvedFightSuccesses(fight,role)" in actions
    assert "strikeKeys=new Set(),blockKeys=new Set()" in actions
    assert "strikes.push({success,damage})" in actions
    assert "blocks.push({blocker:success,target})" in actions
    assert "fightBlockTargets(fight,role,success)" in actions
    assert "capacity>1?`${success.kind}:shield`:`${success.kind}:${target.kind}`" in actions
    assert "Math.random" not in actions
    assert "fightSuccessesFromDice" in APP and "dieIndex:index" in body("fightSuccessesFromDice")
    render = body("renderFightResolution")
    assert "commitFightStrike(fight,role,button.dataset.fightStrike)" in render
    assert "commitFightBlock(fight,role,button.dataset.fightBlocker,[button.dataset.fightBlockTarget])" in render


def test_recent_exchange_uses_committed_history_and_solo_copy_is_explicit():
    record = body("fightResolutionRecordHtml")
    recent = body("fightLastResolutionHtml")
    render = body("renderFightResolution")
    assert "entry.damage" in record and "entry.before" in record and "entry.after" in record
    assert "entry.blockedKinds" in record and "BLOCKED" in record and "STRUCK" in record
    assert "!isPvpMode()" in recent
    assert "fight[latest.role]?.side==='npo'" in recent
    assert "fight[previous.role]?.side==='player'" in recent
    assert "soloExchange?[previous,latest]:[latest]" in recent and "LAST EXCHANGE" in recent
    assert "Guide automatically resolves the NPO’s response" in render
    assert "soloNpoFightDecision" in render
    assert "Continue" not in recent


def test_pvp_and_engine_persistence_contracts_remain_unchanged():
    render = body("renderFightResolution")
    assert "participant.side==='player'||isPvpMode()" in render
    assert "if(!human){const choice=soloNpoFightDecision" in render
    assert "commitFightStrike" in render and "commitFightBlock" in render
    assert "fight.history" in body("normalizeFightState")
    assert "pendingDice" in APP
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_v923_release_surfaces_and_notes_are_consistent():
    expected = CURRENT_APP_VERSION
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert "tomb-world-battle-guide-" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert all(f"{asset}?v={expected}" in INDEX for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ))
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    assert "## v9.2.3" in README
    assert "Removed duplicate equivalent Fight choices." in README
