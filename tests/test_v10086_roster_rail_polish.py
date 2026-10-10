from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def roster_source():
    return APP[
        APP.index("const EXPERIMENTAL_DEATHWATCH_ROSTER_IMAGE_ROOT")
        : APP.index("function showPlayerActivation()")
    ]


def roster_css():
    return CSS.split(
        "Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1
    )[1]


def test_release_surfaces_are_v10086_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 86)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_first_and_last_cells_follow_the_rounded_rail():
    block = roster_css()
    assert 'html[data-ui="tomb"] .experimental-roster-item:first-child{border-radius:8px 0 0 8px}' in block
    assert 'html[data-ui="tomb"] .experimental-roster-item:last-child{border-right:0;border-radius:0 8px 8px 0}' in block
    rail = block.split('html[data-ui="tomb"] .experimental-roster-rail{', 1)[1].split("}", 1)[0]
    assert "border-radius:9px" in rail
    assert "overflow:hidden" in rail


def test_triangle_selection_notch_is_removed():
    source = roster_source()
    assert "experimental-roster-notch" not in source
    assert "experimental-roster-notch" not in roster_css()
    assert 'class="experimental-roster-item selected"' not in source


def test_unselected_detail_reserves_the_selected_stats_footprint():
    source = roster_source()
    assert 'class="experimental-roster-stats placeholder" id="experimentalRosterStats" aria-hidden="true"' in source
    for label in ("APL", "MOVE", "SAVE", "WOUNDS"):
        assert f"<small>{label}</small><strong>—</strong>" in source
    assert 'id="experimentalRosterStats" hidden' not in source
    assert "stats.classList.remove('placeholder');" in source
    assert "stats.removeAttribute('aria-hidden');" in source
    assert "stats.hidden=false" not in source

    block = roster_css()
    assert 'html[data-ui="tomb"] .experimental-roster-stats.placeholder{' in block
    placeholder = block.split(
        'html[data-ui="tomb"] .experimental-roster-stats.placeholder{', 1
    )[1].split("}", 1)[0]
    assert "visibility:hidden" in placeholder


def test_detail_copy_reserves_the_same_mobile_footprint_before_and_after_selection():
    source = roster_source()
    assert '<p id="experimentalRosterDetailRole">Select an operative above.</p>' in source

    block = roster_css()
    detail = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-copy>p:not(.eyebrow){', 1
    )[1].split("}", 1)[0]
    assert "min-height:2.4em" in detail

    mobile = block.split("@media(max-width:600px)", 1)[1].split(
        "@media(max-height:520px)", 1
    )[0]
    heading = mobile.split(
        'html[data-ui="tomb"] .experimental-roster-detail-copy h3{', 1
    )[1].split("}", 1)[0]
    assert "min-height:2.4em" in heading


def test_polish_remains_experimental_only_and_current_picker_is_unchanged():
    picker = APP[
        APP.index("function showPlayerActivation()")
        : APP.index("function playerActivationSummary")
    ]
    assert "document.documentElement.dataset.ui==='tomb'&&selectedPlayerTeamName().toLowerCase()==='deathwatch'" in picker
    assert '<select id="humanPlayerSelection" data-dialog-focus>' in picker
    assert 'html[data-ui="classic"] .experimental-roster' not in CSS
