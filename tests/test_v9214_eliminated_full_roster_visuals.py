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
    start_index = APP.index(start)
    return APP[start_index:APP.index(end, start_index)]


def css_rule(selector):
    start = CSS.index(selector)
    return CSS[start:CSS.index("}", start) + 1]


def test_npo_overlay_is_upper_scoped_and_decorative():
    overlay = css_rule(".npo-roster-grid>.npo-roster-card.dead::after")
    assert 'url("Assets/Images/eliminated-necron-skull.png")' in overlay
    assert 'content:""' in overlay
    assert "position:absolute" in overlay
    assert "top:3.5rem" in overlay and "left:50%" in overlay
    assert "transform:translateX(-50%)" in overlay
    assert "inset:0" not in overlay and "place-items:center" not in overlay
    assert "pointer-events:none" in overlay
    assert ".npo-roster-card.dead::after" not in CSS.replace(
        ".npo-roster-grid>.npo-roster-card.dead::after", ""
    )


def test_eliminated_npo_profile_is_muted_but_remains_interactive():
    profile = source("function npoProfileDetailsHtml", "function npoRosterCard")
    card = source("function npoRosterCard", "function operativeCard")
    muted = css_rule(
        ".npo-roster-grid>.npo-roster-card.dead .npo-profile-details>summary"
    )
    normal = css_rule(".operative-guidance summary")
    assert '<details class="operative-guidance npo-profile-details">' in profile
    assert "<summary>Gameplay profile</summary>" in profile
    assert "disabled" not in profile
    assert "color:var(--muted)" in muted and "var(--green)" not in muted
    assert "color:var(--green)" in normal
    assert "eliminated?'ELIMINATED':" in card


def test_npo_roster_actions_and_elimination_logic_are_unchanged():
    roster = source("function renderRoster", "function renderPlayerRoster")
    card = source("function npoRosterCard", "function operativeCard")
    assert "const eliminated=hasProfile&&n.wounds<=0" in card
    assert "data-wound=" in card and "data-heal=" in card and "data-delete=" in card
    assert "adjustWounds(b.dataset.wound,-1)" in roster
    assert "adjustWounds(b.dataset.heal,1)" in roster
    assert "deleteNpo(b.dataset.delete)" in roster
    assert 'id="addNpo"' in roster and "showAddNpo" in roster


def test_player_overlay_is_upper_scoped_generic_and_decorative():
    player = source("function renderPlayerRoster", "function npoProfileWeaponHtml")
    overlay = css_rule(".player-full-roster-grid>.roster-operative-card.dead::after")
    assert 'class="roster-grid player-full-roster-grid"' in player
    assert "operative-card roster-operative-card ${eliminated?'dead':''}" in player
    assert 'content:"☠"' in overlay
    assert "eliminated-necron-skull.png" not in overlay
    assert "top:3.5rem" in overlay and "left:50%" in overlay
    assert "pointer-events:none" in overlay
    assert ".roster-grid>.roster-operative-card.dead::after" not in CSS
    assert ".roster-operative-card:not(.dead)::after" not in CSS
    assert "eliminated?'ELIMINATED':" in player


def test_player_roster_controls_and_abilities_are_unchanged():
    player = source("function renderPlayerRoster", "function npoProfileWeaponHtml")
    assert "Operative abilities (${abilities.length})" in player
    assert "data-player-wound" in player and "data-player-heal" in player
    assert "adjustPlayerWounds(button.dataset.playerWound,-1)" in player
    assert "adjustPlayerWounds(button.dataset.playerHeal,1)" in player


def test_compact_status_tracker_and_fight_surfaces_have_no_skulls():
    compact_npo = source("function operativeStatusRow", "function renderOperativeStatusPanel")
    tracker = source("function activationTracker", "function showPlayerOperativeStatus")
    fight = source("function fightResultParticipantHtml", "function acknowledgeFightResult")
    for compact in (compact_npo, tracker, fight):
        assert "☠" not in compact
        assert "eliminated-necron-skull.png" not in compact
    assert "operative-status-elimination-icon" not in compact_npo
    assert "tracker-elimination-icon" not in tracker
    assert '<strong class="fight-eliminated">ELIMINATED</strong>' in fight


def test_release_surfaces_are_v9214_and_save_format_is_unchanged():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 14)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
