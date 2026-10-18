"""Keep Deathwatch activation labels readable in the responsive roster rail."""

from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")

DEATHWATCH = APP.split(
    "function experimentalDeathwatchRosterMarkup(candidates", 1
)[1].split("function showPlayerActivation()", 1)[0]
NECRON = APP.split(
    "function showExperimentalNecronRosterRail(candidates)", 1
)[1].split("function experimentalDeathwatchRosterMarkup(candidates", 1)[0]
RULES = CSS.split(
    "/* v10.0.123: Give ready Deathwatch operatives equally wide, scrollable rail tiles. */", 1
)[1].split(
    "/* v10.0.111: Experimental Deathwatch target rail.", 1
)[0]


def rule(selector):
    return RULES.split(selector + "{", 1)[1].split("}", 1)[0]


def test_new_rail_class_only_targets_experimental_deathwatch_activation():
    assert 'class="experimental-roster-rail experimental-deathwatch-roster-rail"' in DEATHWATCH
    assert "experimental-deathwatch-roster-rail" not in NECRON
    assert 'class="experimental-roster-rail experimental-necron-roster-rail' in NECRON
    assert "html[data-ui=\"tomb\"] .experimental-deathwatch-roster-rail{" in RULES
    assert "html[data-ui=\"classic\"] .experimental-deathwatch-roster-rail" not in CSS


def test_rail_scrolls_horizontally_and_equal_tiles_never_shrink_below_120px():
    rail = rule('html[data-ui="tomb"] .experimental-deathwatch-roster-rail')
    item = rule('html[data-ui="tomb"] .experimental-deathwatch-roster-rail .experimental-roster-item')
    assert "overflow-x:auto" in rail
    assert "overflow-y:hidden" in rail
    assert "overscroll-behavior-x:contain" in rail
    assert "scroll-snap-type:x proximity" in rail
    assert "-webkit-overflow-scrolling:touch" in rail
    assert "flex:1 0 120px" in item
    assert "scroll-snap-align:start" in item


def test_full_operatives_names_never_break_midword():
    name = rule('html[data-ui="tomb"] .experimental-deathwatch-roster-rail .experimental-roster-name')
    assert "overflow-wrap:normal" in name
    assert "word-break:normal" in name
    # The existing two-line treatment is retained for names that have spaces.
    assert "-webkit-line-clamp:2" in CSS
    assert "white-space:normal" in CSS


def test_selection_and_detail_behavior_are_preserved():
    assert 'role="radiogroup" aria-label="Ready Deathwatch operatives"' in DEATHWATCH
    assert 'role="radio" aria-checked="false"' in DEATHWATCH
    assert "button.onclick=()=>selectOperative(button.dataset.rosterOperative)" in DEATHWATCH
    assert "['ArrowLeft','ArrowRight','Home','End']" in DEATHWATCH
    assert "selectedId=id" in DEATHWATCH
    assert "confirm.disabled=false" in DEATHWATCH
    assert "experimentalRosterDetailImage" in DEATHWATCH


def test_version_surfaces_are_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
