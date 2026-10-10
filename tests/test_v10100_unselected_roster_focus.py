from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def picker_source():
    return APP.split("function showExperimentalDeathwatchRosterRail(candidates)", 1)[1].split("function showPlayerActivation()", 1)[0]


def test_release_bumps_all_runtime_version_surfaces():
    assert CURRENT_APP_VERSION == "10.0.100"
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_initial_focus_is_on_instructions_not_first_roster_button():
    source = picker_source()
    button_markup = source.split('return `<button type="button" class="experimental-roster-item"', 1)[1].split("</button>`;", 1)[0]
    assert "data-dialog-focus" not in button_markup
    assert 'role="radio" aria-checked="false"' in button_markup
    assert 'tabindex="${index===0?\'0\':\'-1\'}"' in button_markup
    assert '<p class="experimental-roster-instruction" tabindex="-1" data-dialog-focus>' in source
    assert 'let selectedId=\'\';' in source
    assert 'id="confirmExperimentalRosterSelection" disabled' in source


def test_selected_state_and_keyboard_indicators_are_retained():
    source = picker_source()
    assert "button.classList.toggle('selected',selected);" in source
    assert "button.setAttribute('aria-checked',String(selected));" in source
    assert "['ArrowLeft','ArrowRight','Home','End']" in source
    assert "button.onclick=()=>selectOperative" in source
    assert 'html[data-ui="tomb"] .experimental-roster-instruction:focus{outline:none}' in CSS
    assert 'html[data-ui="tomb"] .experimental-roster-item:focus-visible{' in CSS
    assert 'html[data-ui="tomb"] .experimental-roster-item.selected{' in CSS
