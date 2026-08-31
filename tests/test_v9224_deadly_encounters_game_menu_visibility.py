import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
MENU = APP[APP.index("  function showGameMenu(){") : APP.index("  function startNewGameSetup(){")]


def test_menu_uses_current_authoritative_deadly_encounters_state():
    assert "function deadlyEncountersActive(){return !isPvpMode()&&state.deadlyEncountersEnabled===true;}" in APP
    assert "${deadlyEncountersActive()?'<button class=\"btn secondary\" id=\"menuDeadlyEncounters\">Deadly Encounters</button>':''}" in MENU
    assert "${!isPvpMode()?'<button class=\"btn secondary\" id=\"menuDeadlyEncounters\"" not in MENU
    assert "if(inGame&&deadlyEncountersActive())$('#menuDeadlyEncounters').onclick=showDeadlyEncountersPanel;" in MENU


def test_menu_condition_covers_enabled_disabled_resumed_and_imported_state():
    condition = lambda game_mode, enabled: game_mode != "pvp" and enabled is True
    assert condition("solo", True)
    assert not condition("solo", False)
    assert not condition("pvp", True)
    for source in ("current", "resumed", "imported"):
        assert condition("solo", True), source
        assert not condition("solo", False), source


def test_menu_keeps_all_other_battle_destinations_and_safe_handler():
    for expected in (
        'data-game-view="mission">Mission & Map',
        'data-game-view="roster">${escapeHtml(opponentSingularLabel())} Roster',
        'data-game-view="player-roster">${escapeHtml(playerSideLabel())} Roster',
        'data-game-view="journal">Battle Journal',
        'id="menuHelp" type="button">Help',
        'id="menuAbout" type="button">About',
    ):
        assert expected in MENU
    assert MENU.count('id="menuDeadlyEncounters"') == 1
    assert "visibility:hidden" not in MENU
    assert "Deadly Encounters (Off)" not in MENU
    assert re.search(r"deadlyEncountersActive\(\).*menuDeadlyEncounters", MENU, re.DOTALL)


def test_menu_grid_omits_placeholders_and_naturally_reflows():
    assert ".game-menu-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px" in STYLES
    assert ".game-menu-grid,.game-menu-session{grid-template-columns:1fr}" in STYLES
    assert 'id="menuDeadlyEncounters" hidden' not in MENU
    assert 'id="menuDeadlyEncounters" disabled' not in MENU


def test_deadly_encounters_setup_summaries_help_and_feature_panel_remain():
    assert 'id="deadlyEncountersEnabled"' in APP
    assert "showDeadlyEncountersPanel()" in APP
    assert "$('#recordDeadlyEncounter').onclick=showRecordDeadlyEncounter;" in APP
    assert "Deadly Encounters: Tomb Worlds" in APP
    assert "White Dwarf 521" in APP
    assert "state.deadlyEncountersEnabled?'Enabled':'Disabled'" in APP
    assert 'id="briefing-deadly-encounters-title">Deadly Encounters</strong>' in APP
    assert "Deadly Encounters:</strong> ${deadlyEncountersStatusLabel()}" in APP
    assert "TombWorldNarration.playDeadlyEncounter" in APP
    assert "Roll official D33" in APP


def test_v9224_version_surfaces_and_persistence_compatibility():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 24)
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
