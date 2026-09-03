from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
SETUP = APP[APP.index("function setupContent") : APP.index("function runStartingNpoGeneration")]
MAP = APP[APP.index("function boardSvg") : APP.index("function renderGuideMapMarker")]


def test_roster_copy_is_removed_without_changing_roster_controls():
    assert "Build a legal kill team using its current official rules." not in SETUP
    assert "Cooperative team splitting is not currently supported." not in SETUP
    assert 'id="randomPlayerTeam"' in SETUP
    assert 'data-select-player="${o.id}"' in SETUP
    assert 'id="setupNext" ${valid?\'\':\'disabled\'}>Roster Ready' in SETUP


def test_shared_map_copy_and_image_contract():
    assert "Extracted from the Games Workshop mission-pack PDF" not in MAP
    assert "Extracted from the included Games Workshop mission-pack PDF" not in APP
    assert ">MISSION MAP</span>" in MAP
    assert "Battle Guide schematic" in MAP
    assert '<img class="official-map-image"' in MAP
    assert 'alt="Battle Guide board layout for ${escapeHtml(currentMission.name)}"' in MAP
    assert "const imagePath=`Assets/Maps/mission-${missionNumber}.png?v=${APP_VERSION}`;" in MAP
    for mission_number in range(1, 7):
        assert f"`./Assets/Maps/mission-{mission_number:02}.png?v=${{APP_VERSION}}`" in WORKER
    assert APP.count("boardSvg(m.id)") == 2


def test_optional_content_copy_is_condensed_and_variants_remain():
    assert "Choose optional game content" in SETUP
    assert "Choose one variant for this battle. The starting Necron roster is generated after this step." in SETUP
    assert "These choices are saved with the battle." not in SETUP
    assert "Tombs Beyond Counting is an official expansion from White Dwarf 517." not in SETUP
    assert "Tomb World Variant" in SETUP
    assert 'name="tombWorldVariant"' in SETUP
    assert "Object.values(TOMB_WORLD_VARIANTS).filter(variant=>variant.available)" in SETUP


def test_solo_deadly_encounters_checkbox_and_state_contract_remain():
    assert '<label class="check-row deadly-encounters-option"><input id="deadlyEncountersEnabled" type="checkbox"' in SETUP
    assert "${state.deadlyEncountersEnabled?'checked':''}" in SETUP
    assert "$('#deadlyEncountersEnabled')?.addEventListener('change',e=>{if(isPvpMode())return;state.deadlyEncountersEnabled=e.target.checked;save();render();});" in APP
    assert "function deadlyEncountersActive(){return !isPvpMode()&&state.deadlyEncountersEnabled===true;}" in APP


def test_pvp_optional_content_omits_deadly_encounters_entirely():
    assert "const deadlyOption=isPvpMode()?''" in SETUP
    assert "Deadly Encounters: Tomb Worlds is available in Solo battles only." not in SETUP
    pvp_markup = SETUP[SETUP.index("const deadlyOption=isPvpMode()?") : SETUP.index(": `<label class=\"check-row deadly-encounters-option\"")]
    assert "<input" not in pvp_markup
    assert "<label" not in pvp_markup
    assert "tabindex" not in pvp_markup
    assert "pvp-unavailable-option" not in STYLES
    assert ".section-note" not in STYLES


def test_pvp_mission_briefing_help_and_game_menu_omit_deadly_encounters():
    assert "const deadlyBriefing=isPvpMode()?'':`<section" in SETUP
    assert "</section>${deadlyBriefing}<small class=\"optional-rules-instruction\">" in SETUP
    assert "${isPvpMode()?'':'<details><summary>Deadly Encounters: Tomb Worlds</summary>" in APP
    assert "if(isPvpMode())return;\n    const de=state.deadlyEncountersState" in APP
    assert "${deadlyEncountersActive()?'<button class=\"btn secondary\" id=\"menuDeadlyEncounters\">Deadly Encounters</button>':''}" in APP


def test_pvp_stale_enabled_state_remains_inactive_without_state_rewrite():
    assert "function deadlyEncountersActive(){return !isPvpMode()&&state.deadlyEncountersEnabled===true;}" in APP
    assert "function deadlyEncountersStatusLabel(){return deadlyEncountersActive()?'On':'Off';}" in APP
    assert "merged.deadlyEncountersEnabled=raw.deadlyEncountersEnabled===true;" in APP
    assert "state.deadlyEncountersEnabled=false" not in SETUP


def test_shared_optional_rules_remain_available_in_both_modes():
    assert 'id="restlessTombEnabled" type="checkbox"' in SETUP
    assert 'name="tombWorldVariant"' in SETUP
    assert "isPvpMode()?'':`<label class=\"check-row restless-tomb-option" not in SETUP


def test_release_note_describes_complete_pvp_removal():
    assert "Removed Solo-only Deadly Encounters references from PvP screens." in README


def test_release_version_cache_and_save_compatibility():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 28)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
