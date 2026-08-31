from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def test_fight_result_uses_eliminated_status_without_changing_fight_state():
    card = source("function fightResultParticipantHtml", "function acknowledgeFightResult")
    result = source("function buildFightResult", "function fightResultParticipantHtml")
    assert '<strong class="fight-eliminated">ELIMINATED</strong>' in card
    assert "INCAPACITATED" not in card
    assert "participant.incapacitated" in card
    assert "attackerIncapacitated:fight.attacker.wounds<=0" in result
    assert "defenderIncapacitated:fight.defender.wounds<=0" in result


def test_dashboard_and_roster_cards_expose_eliminated_as_text():
    panel = source("function operativeStatusRow", "function renderOperativeStatusPanel")
    tracker = source("function activationTracker", "function showPlayerOperativeStatus")
    roster = source("function renderPlayerRoster", "function npoProfileWeaponHtml")
    assert "status==='ELIMINATED'" in panel
    assert "<span class=\"operative-status-value\">${status}</span>" in panel
    assert tracker.count("<strong>${status}</strong>") == 1
    assert "<strong>${trackerStatus.status}</strong>" in tracker
    assert "eliminated?'ELIMINATED':" in roster
    npo_roster = source("function npoRosterCard", "function operativeCard")
    assert "eliminated?'ELIMINATED':" in npo_roster
    assert 'operative-status-badge ${status.toLowerCase()' in roster


def test_key_defeated_status_surfaces_do_not_mix_incapacitated_wording():
    fight_card = source("function fightResultParticipantHtml", "function acknowledgeFightResult")
    mission_status = source("const missionProgressRenderers", "function missionProgressHtml")
    assert "INCAPACITATED" not in fight_card
    assert "'Incapacitated'" not in mission_status
    assert "?'Eliminated':'Still in the killzone'" in mission_status


def test_defeated_cards_render_no_skull_icon_or_icon_gap():
    card_sources = "\n".join((
        source("function operativeStatusRow", "function renderOperativeStatusPanel"),
        source("function activationTracker", "function showPlayerOperativeStatus"),
        source("function renderPlayerRoster", "function npoProfileWeaponHtml"),
    ))
    assert "☠" not in card_sources
    assert "tracker-elimination-icon" not in card_sources
    assert "operative-status-elimination-icon" not in card_sources
    assert ".npo-roster-grid>.npo-roster-card.dead::after" in CSS
    assert ".operative-card.dead:after" not in CSS
    assert ".operative-status-row.eliminated{padding-left" not in CSS


def test_defeated_card_red_styling_and_zero_wounds_remain():
    assert ".tracker-operative.eliminated," in CSS
    assert "border:2px solid var(--danger)" in CSS
    assert ".tracker-operative.eliminated strong" in CSS
    assert ".operative-status-badge.eliminated" in CSS
    roster = source("function npoRosterCard", "function operativeCard")
    assert "const wounds=hasProfile?`${n.wounds}/${n.maxWounds}`:'—'" in roster
    assert "class=\"${eliminated?'zero-wounds':''}\"" in roster


def test_non_defeated_statuses_are_unchanged():
    panel = source("function npoTrackerStatus", "function statusWoundsHtml")
    tracker = source("function activationTracker", "function showPlayerOperativeStatus")
    roster = source("function npoRosterCard", "function operativeCard")
    for status in ("ACTIVE", "READY", "RESERVE"):
        assert status in panel + tracker + roster


def test_release_version_and_persistence_surfaces():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 10)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
        assert f'{asset}?v={CURRENT_APP_VERSION}' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
