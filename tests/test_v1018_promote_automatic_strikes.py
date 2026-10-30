"""Standard and Experimental must share automatic Fight Strike explanations."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def function_body(name, next_marker):
    start = APP.index("  function " + name + "(")
    end = APP.index(next_marker, start)
    return APP[start:end]


def test_automatic_strike_result_shared():
    body = function_body("experimentalFightAutomaticStrikeResultHtml", "  // Keep the full saved explanation")
    assert "experimentalFeaturesEnabled()" not in body
    assert "isPvpMode()" in body
    assert "dataset.ui!=='tomb'" in body
    assert "entry.automatic" in body
    assert "STRIKES RESOLVED" in body
    assert "${experimentalFightAutomaticStrikeResultHtml(result)}" in APP


def test_automatic_strike_preview_shared():
    body = function_body("experimentalFightAutomaticStrikePreview", "  function experimentalFightStrikeAdvice")
    assert "experimentalFeaturesEnabled()" not in body
    assert "isPvpMode()" in body
    assert "dataset.ui!=='tomb'" in body
    assert "unresolvedFightSuccesses" in body
    assert "target.wounds<=damage" in body
    assert "experimentalFightAutomaticStrikePreview(fight,role,success,damage)" in APP


def test_shared_styles_and_version():
    section = CSS.split("/* v10.1.8: Automatic residual Fight strike explanations shared", 1)[1].split("/* v10.0.175/180:", 1)[0]
    assert '[data-experimental="on"]' not in section
    assert 'html[data-ui="tomb"] .fight-auto-strike-result' in section
    for text in (APP, SW, HTML):
        assert "10.1.8" in text
    assert "10.1.7" not in HTML
    assert "Experimental Mode is reserved for future previews." in HTML
