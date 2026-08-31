from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def css_rule(selector):
    start = CSS.index(selector)
    return CSS[start:CSS.index("}", start) + 1]


def test_full_roster_dead_cards_receive_the_decorative_necron_overlay_only():
    roster = source("function renderRoster", "function npoProfileWeaponHtml")
    card = source("function npoRosterCard", "function operativeCard")
    overlay = css_rule(".npo-roster-grid>.npo-roster-card.dead::after")
    assert 'class="player-roster-grid npo-roster-grid"' in roster
    assert "npoRosterCard(n,n.battlefieldState==='deployed'||n.wounds<=0)" in roster
    assert "const eliminated=hasProfile&&n.wounds<=0" in card
    assert "npo-roster-card ${eliminated?'dead':''}" in card
    assert 'url("Assets/Images/eliminated-necron-skull.png")' in overlay
    assert 'content:""' in overlay
    assert "pointer-events:none" in overlay
    assert "position:absolute" in overlay and "inset:0" in overlay
    assert "6rem" in overlay and "opacity:.55" in overlay
    assert ".npo-roster-card.dead::after" not in CSS.replace(
        ".npo-roster-grid>.npo-roster-card.dead::after", ""
    )
    assert ".npo-roster-card:not(.dead)::after" not in CSS


def test_full_roster_keeps_eliminated_text_wounds_border_and_controls():
    card = source("function npoRosterCard", "function operativeCard")
    assert "eliminated?'ELIMINATED':" in card
    assert "const wounds=hasProfile?`${n.wounds}/${n.maxWounds}`:'—'" in card
    assert "class=\"${eliminated?'zero-wounds':''}\"" in card
    assert ".npo-roster-card.dead," in CSS
    assert "border:2px solid var(--danger)" in CSS
    for control in ('data-wound=', 'data-heal=', 'data-delete='):
        assert control in card
    assert "Gameplay profile" in source("function npoProfileDetailsHtml", "function npoRosterCard")
    render = source("function renderRoster", "function npoProfileWeaponHtml")
    assert "adjustWounds(b.dataset.wound,-1)" in render
    assert "adjustWounds(b.dataset.heal,1)" in render
    assert "deleteNpo(b.dataset.delete)" in render
    assert "id=\"addNpo\"" in render and "showAddNpo" in render


def test_compact_dashboard_remains_text_only_without_icon_space():
    panel = source("function operativeStatusRow", "function renderOperativeStatusPanel")
    assert "status==='ELIMINATED'" in panel
    assert "<span class=\"operative-status-value\">${status}</span>" in panel
    assert "eliminated-necron-skull.png" not in panel
    assert "operative-status-elimination-icon" not in panel
    assert ".operative-status-row.eliminated" in CSS
    assert ".operative-status-row.eliminated{padding-left" not in CSS


def test_tracker_fight_result_and_player_cards_remain_skull_free():
    tracker = source("function activationTracker", "function showPlayerOperativeStatus")
    fight = source("function fightResultParticipantHtml", "function acknowledgeFightResult")
    player = source("function renderPlayerRoster", "function npoProfileWeaponHtml")
    assert "<strong>${trackerStatus.status}</strong>" in tracker
    assert "tracker-elimination-icon" not in tracker
    assert '<strong class="fight-eliminated">ELIMINATED</strong>' in fight
    assert "eliminated-necron-skull.png" not in fight
    assert "☠" not in tracker + fight + player + CSS
    assert ".operative-card.dead:after" not in CSS


def test_release_surfaces_and_persistence_are_v9213_compatible():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 13)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "tomb-world-battle-guide-';" in WORKER
    assert "'./Assets/Images/eliminated-necron-skull.png'" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert (ROOT / "Assets/Images/eliminated-necron-skull.png").is_file()
