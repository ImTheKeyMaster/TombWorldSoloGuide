import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
REGENERATION_NOTICE = APP[
    APP.index("function showRegenerationNotice") : APP.index("importInput.addEventListener")
]
MAP_RENDERER = APP[APP.index("function boardSvg") : APP.index("function renderGuideMapMarker")]


def test_incompatible_battle_toasts_are_clear_and_source_specific():
    assert "Legacy battle returned to setup." not in APP
    assert "Save imported and returned to setup." not in APP
    assert "Previous battle could not be resumed. Your setup choices were preserved." in REGENERATION_NOTICE
    assert "Imported battle could not be resumed. Your setup choices were preserved." in REGENERATION_NOTICE
    assert "source==='import'?" in REGENERATION_NOTICE


def test_regeneration_flow_and_modal_copy_are_unchanged():
    assert "Current battle cannot be resumed" in REGENERATION_NOTICE
    assert '>Return to Setup</button>' in REGENERATION_NOTICE
    assert "const reset=resetActiveBattle(migration.state);closeModal();" in REGENERATION_NOTICE
    assert "commitImported(reset,{...migration.report,requiresRegeneration:true})" in REGENERATION_NOTICE
    assert "const causes=[...migration.report.unsupportedRetiredTypes,...migration.report.invalidPhysicalLimits,...migration.report.errors];" in REGENERATION_NOTICE


def test_migration_detection_and_setup_preservation_behavior_remain():
    script = r"""
const assert=require('assert');
const p=require('./persistence.js');
const catalog={'Canoptek Tomb Crawler':{name:'Canoptek Tomb Crawler',wounds:21,physicalQuantity:2,loadoutOptions:[{id:'twin-gauss-reapers'}]}};
const migrated=p.migrateSaveDetailed({saveVersion:3,missionId:'04',playerTeamId:'death-korps',playerRoster:['trooper'],settings:{sound:false},preferences:{motion:false},roster:[{id:'retired-1',type:'Crypt Sentinel',wounds:8}]},catalog);
assert.equal(migrated.report.requiresRegeneration,true);
assert.deepEqual(migrated.report.unsupportedRetiredTypes,['Crypt Sentinel']);
const reset=p.resetActiveBattle(migrated.state);
assert.equal(reset.missionId,'04');
assert.equal(reset.playerTeamId,'death-korps');
assert.deepEqual(reset.playerRoster,['trooper']);
assert.deepEqual(reset.settings,{sound:false});
assert.deepEqual(reset.preferences,{motion:false});
assert.deepEqual(reset.roster,[]);
assert.equal(reset.screen,'setup');
assert.equal(reset.turningPoint,0);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_shared_official_map_renderer_removes_only_the_file_path_caption():
    assert "<figcaption" not in MAP_RENDERER
    assert "Only the map for this mission is shown." not in APP
    assert "The complete official PDF is stored locally in" not in APP
    assert "Assets/Tomb-World-Mission-Pack.pdf" not in APP
    assert '<figure class="official-map-card">' in MAP_RENDERER
    assert "OFFICIAL MISSION MAP" in MAP_RENDERER
    assert "${escapeHtml(currentMission.number)} · ${escapeHtml(currentMission.name)}" in MAP_RENDERER
    assert "Extracted from the Games Workshop mission-pack PDF" in MAP_RENDERER
    assert '<img class="official-map-image"' in MAP_RENDERER
    assert 'alt="Official board layout for ${escapeHtml(currentMission.name)}"' in MAP_RENDERER
    assert ".official-map-card figcaption" not in STYLES
    assert ".official-map-card code" not in STYLES


def test_all_shared_map_surfaces_still_render_the_same_map():
    assert APP.count("boardSvg(m.id)") == 2
    setup = APP[APP.index("function setupContent") : APP.index("function runStartingNpoGeneration")]
    mission_view = APP[APP.index("function renderMission") : APP.index("function renderRoster")]
    assert "board setup" in setup
    assert "${boardSvg(m.id)}" in setup
    assert "${boardSvg(m.id)}" in mission_view
    assert "Mission rules" in mission_view
    assert "Victory" in mission_view


def test_map_keeps_its_responsive_mobile_image_contract_without_caption_space():
    assert ".official-map-image{\n  display:block;\n  width:100%;\n  height:auto;" in STYLES
    assert ".official-map-card{margin-inline:-2px;border-radius:13px}" in STYLES
    assert "figcaption" not in MAP_RENDERER


def test_v9225_version_cache_and_save_compatibility_surfaces():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 25)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "./Assets/Tomb-World-Mission-Pack.pdf" not in WORKER
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
