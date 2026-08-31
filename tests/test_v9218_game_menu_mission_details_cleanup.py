from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


GAME_MENU = section("function showGameMenu", "function confirmNewGame")
MISSION_DETAILS = section("function missionDetailsContentFallback", "function showMissionResult")
MISSION_VIEW = section("function renderMission", "function renderRoster")
GUIDED_PLAY_BINDINGS = section("function bindPlay", "function showCeaselessScuttling")


def test_game_menu_removes_only_the_redundant_mission_details_entry():
    assert "menuMissionDetails" not in GAME_MENU
    assert ">Mission Details</button>" not in GAME_MENU
    assert 'data-game-view="mission">Mission & Map</button>' in GAME_MENU
    assert 'data-game-view="play">Return to Guided Play</button>' in GAME_MENU


def test_game_menu_preserves_solo_only_deadly_encounters_behavior():
    assert "${!isPvpMode()?'<button class=\"btn secondary\" id=\"menuDeadlyEncounters\">Deadly Encounters</button>':''}" in GAME_MENU
    assert "if(inGame&&!isPvpMode())$('#menuDeadlyEncounters').onclick=showDeadlyEncountersPanel;" in GAME_MENU


def test_compact_mission_details_modal_and_status_content_remain_available():
    assert "function missionDetailsContentFallback()" in MISSION_DETAILS
    assert "function missionDetailsContent()" in MISSION_DETAILS
    assert "function showMissionDetails()" in MISSION_DETAILS
    assert "Recent Activity" in MISSION_DETAILS
    assert "Final Progress" in MISSION_DETAILS
    assert "completedTurningPoint" in MISSION_DETAILS
    assert "Completed during" in MISSION_DETAILS
    assert "showModal(completed?'MISSION STATUS':'MISSION DETAILS',content)" in MISSION_DETAILS


def test_guided_play_mission_hud_still_opens_mission_details():
    assert "$('#missionHud')?.addEventListener('click',showMissionDetails);" in GUIDED_PLAY_BINDINGS


def test_mission_and_map_reference_content_is_preserved():
    for content in (
        "function renderMission()",
        "${boardSvg(m.id)}",
        "Battle settings",
        "Mission rules",
        "Victory",
        "${missionProgressHtml()}",
        "TP1 Initiative",
    ):
        assert content in MISSION_VIEW


def test_release_surfaces_and_save_schema_are_consistent():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 18)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
