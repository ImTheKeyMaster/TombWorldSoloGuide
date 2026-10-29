"""Desktop Fight Resolution VS badge must not overlap operative wound counts."""
import math
import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_wide_solo_fight_reserves_vs_diamond_gutter():
    """Badge's rotated outline fits entirely inside the reserved desktop gap."""
    start = CSS.index("/* v10.1.1: On desktop and wide touch screens")
    end = CSS.index("/* Each swipeable tile", start)
    fix = CSS[start:end]

    # Standard and Experimental are the same Solo layout; PvP and other
    # dialogs must not receive the gutter.
    assert 'html[data-ui="tomb"] .experimental-fight-choice-screen.is-duel-layout .experimental-fight-pools' in fix
    assert "gap:56px;" in fix
    assert "(min-width:600px) and (min-height:520px)" in fix
    assert "(min-width:480px) and (hover:hover) and (pointer:fine)" in fix
    assert ".experimental-fight-versus" not in fix, "VS badge itself must not move"

    # The 35px badge has a 2px inset rotated square. The corner-to-corner
    # visual width should remain comfortably smaller than the desktop gutter.
    badge = CSS.split('html[data-ui="tomb"] .is-duel-layout .experimental-fight-versus{', 1)[1].split("}", 1)[0]
    diamond = CSS.split('html[data-ui="tomb"] .is-duel-layout .experimental-fight-versus::before{', 1)[1].split("}", 1)[0]
    assert "left:50%;top:50%" in badge
    assert "width:35px;height:35px" in badge
    assert "inset:2px" in diamond
    assert "rotate(45deg)" in diamond
    visual_diameter = (35 - 2 * 2) * math.sqrt(2)
    assert (56 - visual_diameter) / 2 >= 5, "VS diamond needs clearance on both sides"


def test_phone_still_uses_original_central_vs_spacing():
    # The default is the approved phone design. Wider gaps only activate in
    # a wide viewport or on a desktop-class fine pointer.
    layout = CSS.split('html[data-ui="tomb"] .experimental-fight-choice-screen.is-duel-layout .experimental-fight-pools{', 1)[1].split("}", 1)[0]
    assert "gap:10px" in layout
    assert 'html[data-ui="tomb"] .is-duel-layout .experimental-fight-versus span' in CSS
    assert "experimental-fight-card-dice" in CSS
    assert "function experimentalFightPoolHtml(" in APP


def test_release_cache_and_both_mode_fight_dice_remain_current():
    assert CURRENT_APP_VERSION == "10.1.1"
    assert "const APP_VERSION = '10.1.1';" in APP
    assert "const APP_VERSION = '10.1.1';" in WORKER
    assert "app.js?v=10.1.1" in INDEX
    assert "styles.css?v=10.1.1" in INDEX
    assert "V10.1.1" in INDEX
    pool = APP.split("  function experimentalFightPoolHtml(", 1)[1].split(
        "  function experimentalFightResolutionHtml(", 1
    )[0]
    assert 'const successesHtml=`<div class="experimental-fight-card-successes experimental-fight-card-dice"' in pool
    assert "experimentalFeaturesEnabled()" not in pool
