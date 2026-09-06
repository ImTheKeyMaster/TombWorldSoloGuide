from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_surfaces_and_cache_busting_are_v9251():
    expected = CURRENT_APP_VERSION
    assert tuple(map(int, expected.split("."))) >= (9, 2, 51)
    assert f"const APP_VERSION = '{expected}';" in (ROOT / "service-worker.js").read_text()
    index = (ROOT / "index.html").read_text()
    assert f'<div class="version">V{expected}</div>' in index
    assert index.count(f"?v={expected}") == 10
    assert (ROOT / "README.md").read_text().startswith(
        f"# Tomb World Battle Guide v{expected}\n\n## v{expected}"
    )
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_awakened_room_selector_uses_only_canonical_room_labels():
    selector = section("function unawakenedScoutRooms", "async function performAwakenRoom")
    assert "SELECT AWAKENED ROOM" in selector
    assert "${escapeHtml(room.label)}</button>" in selector
    assert "room.label.toUpperCase()" not in selector
    button = selector.split('data-select-awakened-room=', 1)[1].split("</button>", 1)[0]
    assert "<small>" not in button
    assert "Unopened" not in button
    assert "Available" not in button
    assert "Ready" not in button


def test_awakened_room_selector_filter_and_single_selection_are_preserved():
    selector = section("function unawakenedScoutRooms", "async function performAwakenRoom")
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    assert "missionEngine().rooms.filter(room=>!state.missionState?.awakenedRooms?.[room.id])" in selector
    assert "unawakenedScoutRooms().some(room=>room.id===roomId)" in awakening
    assert "if(state.missionState?.awakenedRooms?.[roomId])" in awakening
    assert "button.disabled=true;void performAwakenRoom(button.dataset.selectAwakenedRoom)" in selector
    assert "state.missionState.pendingAwakening=null" in awakening
    assert "scoutedRoomIds" not in awakening


def test_room_lifecycle_status_remains_in_mission_details():
    details = section("scout:(engine,progress,{readOnly", "regroup:(engine,progress,{readOnly")
    assert "'Unopened'" in details
    assert "Awakened · Unscouted" in details
    assert "Scouted" in details


def test_generic_action_completion_is_two_button_and_damage_free():
    completion = section("function showPendingHumanPlayerActionCompletion", "function commitHumanPlayerAction")
    assert "Apply Other Damage" not in completion
    assert "pendingActionOtherDamage" not in completion
    assert completion.count('<button class="btn') == 2
    assert "cancelCurrentHumanPlayerAction" in completion
    assert "completePlayerActivation(stage)" in completion
    descriptions = section("function selectHumanPlayerAction", "function showPendingHumanPlayerActionCompletion")
    assert "Confirm that Operate Hatch is complete." in descriptions
    assert "Confirm that Breach is complete." in descriptions


def test_other_damage_is_absent_from_all_activation_ui_and_action_catalog():
    shell = section("function renderHumanActivationShell", "function renderHumanPlayerActionPicker")
    catalog = section("function playerHumanActionCatalog", "function playerHumanActionState")
    assert "Apply Other Damage" not in APP
    assert "Other Damage" not in shell + catalog
    assert "name:'Other Damage'" not in catalog
    assert "Special Actions" not in catalog


def test_roster_wound_adjustment_and_save_compatibility_remain_available():
    roster = section("function renderPlayerRoster", "function npoProfileWeaponHtml")
    adjustment = "function adjustPlayerWounds" + section("function adjustPlayerWounds", "function adjustWounds")
    persistence = section("function save", "async function load")
    assert "data-player-wound" in roster and "data-player-heal" in roster
    assert "adjustPlayerWounds" in roster
    assert "state.playerWounds[id]=wounds" in adjustment
    assert "if(wounds===0)" in adjustment
    assert "localStorage.setItem(STORAGE_KEY" in persistence
