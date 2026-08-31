from pathlib import Path
import re

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


def rem_value(rule, property_name):
    match = re.search(rf"{property_name}:(\d+(?:\.\d+)?)rem", rule)
    assert match
    return float(match.group(1))


def test_full_roster_skulls_are_the_top_local_noninteractive_layer():
    player = css_rule(".player-full-roster-grid>.roster-operative-card.dead::after")
    npo = css_rule(".npo-roster-grid>.npo-roster-card.dead::after")
    for overlay in (player, npo):
        assert "position:absolute" in overlay
        assert "z-index:2" in overlay
        assert "pointer-events:none" in overlay
        assert "9999" not in overlay
    assert "position:relative" in css_rule(".operative-card")
    assert "position:relative" in css_rule(".npo-roster-card{")
    assert ".player-full-roster-grid>.roster-operative-card>*" not in CSS
    assert ".npo-roster-card>*" not in CSS


def test_necron_and_player_skulls_have_comparable_visual_footprints():
    player = css_rule(".player-full-roster-grid>.roster-operative-card.dead::after")
    npo = css_rule(".npo-roster-grid>.npo-roster-card.dead::after")
    assert rem_value(player, "font-size") == 5.5
    assert rem_value(player, "width") == rem_value(player, "height") == 5.5
    assert rem_value(npo, "width") == rem_value(npo, "height") == 7.5
    assert rem_value(npo, "width") > 5.5
    assert 1.25 <= rem_value(npo, "width") / rem_value(player, "font-size") <= 1.5
    assert "background-size" not in npo
    assert "center/contain no-repeat" in npo


def test_skulls_remain_centered_in_the_upper_stat_region():
    player = css_rule(".player-full-roster-grid>.roster-operative-card.dead::after")
    npo = css_rule(".npo-roster-grid>.npo-roster-card.dead::after")
    for overlay in (player, npo):
        assert "top:3.5rem" in overlay
        assert "left:50%" in overlay
        assert "transform:translateX(-50%)" in overlay
        assert "inset:0" not in overlay
    assert "Gameplay profile" not in npo
    assert "Operative abilities" not in player


def test_npo_profile_stays_muted_when_dead_and_green_when_active():
    profile = source("function npoProfileDetailsHtml", "function npoRosterCard")
    muted = css_rule(".npo-roster-grid>.npo-roster-card.dead .npo-profile-details>summary")
    active = css_rule(".operative-guidance summary")
    assert '<details class="operative-guidance npo-profile-details">' in profile
    assert "<summary>Gameplay profile</summary>" in profile
    assert "disabled" not in profile
    assert "color:var(--muted)" in muted
    assert "color:var(--green)" in active
    assert 'url("Assets/Images/eliminated-necron-skull.png")' in css_rule(
        ".npo-roster-grid>.npo-roster-card.dead::after"
    )


def test_player_skull_is_generic_dead_full_roster_decoration_only():
    player_render = source("function renderPlayerRoster", "function npoProfileWeaponHtml")
    overlay = css_rule(".player-full-roster-grid>.roster-operative-card.dead::after")
    assert 'content:"☠"' in overlay
    assert "eliminated-necron-skull.png" not in overlay
    assert "${eliminated?'dead':''}" in player_render
    assert ".roster-operative-card:not(.dead)::after" not in CSS


def test_compact_dashboard_tracker_status_and_fight_remain_skull_free():
    compact = source("function operativeStatusRow", "function renderOperativeStatusPanel")
    tracker = source("function activationTracker", "function showPlayerOperativeStatus")
    fight = source("function fightResultParticipantHtml", "function acknowledgeFightResult")
    for surface in (compact, tracker, fight):
        assert "eliminated-necron-skull.png" not in surface
        assert "☠" not in surface
    assert "operative-status-elimination-icon" not in compact
    assert "tracker-elimination-icon" not in tracker
    assert '<strong class="fight-eliminated">ELIMINATED</strong>' in fight


def test_all_release_surfaces_are_v9215_and_save_schema_is_unchanged():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 15)
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
