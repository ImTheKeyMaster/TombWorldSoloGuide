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


def test_shared_official_map_copy_and_image_contract():
    assert "Extracted from the Games Workshop mission-pack PDF" in MAP
    assert "Extracted from the included Games Workshop mission-pack PDF" not in APP
    assert "OFFICIAL MISSION MAP" in MAP
    assert '<img class="official-map-image"' in MAP
    assert 'alt="Official board layout for ${escapeHtml(currentMission.name)}"' in MAP
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


def test_pvp_deadly_encounters_is_muted_noninteractive_information():
    expected = '<div class="check-row deadly-encounters-option pvp-unavailable-option"><span><strong>Deadly Encounters: Tomb Worlds (Solo battles only)</strong></span></div>'
    assert expected in SETUP
    assert "Deadly Encounters: Tomb Worlds is available in Solo battles only." not in SETUP
    pvp_markup = SETUP[SETUP.index("const deadlyOption=isPvpMode()?") : SETUP.index(": `<label class=\"check-row deadly-encounters-option\"")]
    assert "<input" not in pvp_markup
    assert "<label" not in pvp_markup
    assert "tabindex" not in pvp_markup
    assert ".pvp-unavailable-option{color:var(--muted);opacity:.6}" in STYLES


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
