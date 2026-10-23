from pathlib import Path
import json

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
SERGEANT = ROOT / "Assets" / "Images" / "TombUI" / "Deathwatch" / "Deathwatch_sergeant.png"
DEATHWATCH = json.loads((ROOT / "Player_Operatives" / "DeathWatch.json").read_text(encoding="utf-8"))


def roster_source():
    return APP[
        APP.index("const DEATHWATCH_PORTRAIT_ROOT")
        : APP.index("function showPlayerActivation()")
    ]


def test_release_surfaces_are_v10085_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 85)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_sergeant_uses_approved_green_portrait_source():
    source = roster_source()
    assert "DEATHWATCH_PORTRAIT_ROOT" in source
    assert "Deathwatch_sergeant.png" in source
    assert SERGEANT.is_file()
    assert SERGEANT.stat().st_size > 100000
    assert "./Assets/Images/TombUI/Deathwatch/Deathwatch_sergeant.png" in WORKER
    assert "DeathwatchRoster/" not in source
    assert "DeathwatchActivation/" not in source


def test_roster_portraits_use_bottom_aligned_contain_not_cover():
    block = CSS.split("Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1)[1]
    image = block.split('html[data-ui="tomb"] .experimental-roster-image img{', 1)[1].split("}", 1)[0]
    assert "object-fit:contain" in image
    assert "object-position:center bottom" in image
    assert "object-fit:cover" not in image


def test_phone_portrait_height_matches_the_five_slot_roster():
    assert DEATHWATCH["rosterSize"] == 5
    assert 'height:min(64px,calc((100vw - 90px)/5))' in CSS


def test_detail_panel_has_visible_stand_in_before_selection():
    source = roster_source()
    assert 'class="experimental-roster-detail-image placeholder"' in source
    assert 'class="experimental-roster-detail-image placeholder" id="experimentalRosterDetailImage"' in source
    assert '<img src="Assets/icon-192.png" alt="">' in source
    assert "detailImage.classList.remove('placeholder')" in source
    assert "confirmExperimentalRosterSelection" in source


def test_detail_placeholder_is_dimmed_and_selected_portrait_bottom_aligned():
    block = CSS.split("Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1)[1]
    detail = block.split('html[data-ui="tomb"] .experimental-roster-detail-image img{', 1)[1].split("}", 1)[0]
    assert "object-fit:contain" in detail
    assert "object-position:center bottom" in detail
    placeholder = block.split('html[data-ui="tomb"] .experimental-roster-detail-image.placeholder img{', 1)[1].split("}", 1)[0]
    assert "opacity:.28" in placeholder
    assert "object-position:center" in placeholder


def test_fix_remains_experimental_only_and_current_picker_is_unchanged():
    source = APP[APP.index("function showPlayerActivation()") : APP.index("function playerActivationSummary")]
    assert "if(usesPlayerPortraitRail()){" in source
    assert '<select id="humanPlayerSelection" data-dialog-focus>' in source
    assert 'html[data-ui="classic"] .experimental-roster' not in CSS
