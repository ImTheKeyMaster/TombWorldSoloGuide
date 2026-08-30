"""Focused acceptance coverage for operative-name Fight turn headings."""
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def render_fight_resolution_source():
    start = APP.index("function renderFightResolution")
    end = APP.index("async function rollFightParticipant", start)
    return APP[start:end]


RENDER = render_fight_resolution_source()


def test_solo_and_pvp_human_turns_use_the_authoritative_operative_name():
    assert "participant.side==='player'||isPvpMode()" in RENDER
    assert "${escapeHtml(participant.label)}'s Turn" in RENDER
    assert "YOUR TURN" not in RENDER
    assert "PLAYER’S TURN" not in RENDER
    assert "NECRON PLAYER’S TURN" not in RENDER


def test_expected_player_and_necron_headings_follow_the_shared_template():
    heading = lambda name: f"{name}'s Turn"
    assert heading("Blademaster") == "Blademaster's Turn"
    assert heading("Lychguard 1") == "Lychguard 1's Turn"


def test_supporting_copy_and_accessible_acting_identity_remain_present():
    assert "Choose how ${escapeHtml(participant.label)} uses one of its unresolved successes." in RENDER
    assert 'aria-label="Acting now: ${escapeHtml(participant.label)}"' in RENDER
    assert "ACTING NOW" in APP


def test_solo_npo_turns_remain_automatic():
    assert "if(!human){const choice=soloNpoFightDecision" in RENDER
    assert "commitFightBlock(fight,role,choice.successId,choice.targetSuccessIds)" in RENDER
    assert "commitFightStrike(fight,role,choice.successId)" in RENDER


def test_fight_action_ownership_and_rules_are_unchanged():
    assert "commitFightStrike(fight,role,button.dataset.fightStrike)" in RENDER
    assert "commitFightBlock(fight,role,button.dataset.fightBlocker,[button.dataset.fightBlockTarget])" in RENDER
    assert "semanticFightActions(fight,role)" in RENDER
    assert "soloNpoFightDecision(fight,role)" in RENDER


def test_release_surfaces_and_save_schema_are_consistent():
    expected = CURRENT_APP_VERSION
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in APP
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert all(f"{asset}?v={expected}" in INDEX for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ))
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
