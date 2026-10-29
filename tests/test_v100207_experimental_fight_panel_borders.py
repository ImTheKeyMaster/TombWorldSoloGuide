"""Experimental-only combatant panel framing regression (v10.0.207).

The two combatants are status displays, not controls. Their outside edges
must not resemble selectable buttons. Standard/PvP and choices are unaffected.
"""
from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_both_experimental_combatant_cards_have_no_border_glow_or_fill():
    start = "/* v10.0.207: Experimental Solo Fight combatants are informational,"
    block = CSS.split(start, 1)[1]
    selector = 'html[data-ui="tomb"][data-experimental="on"] .is-duel-layout .experimental-fight-pool'
    assert selector + "," in block
    assert selector + ".active{" in block
    match = re.search(re.escape(selector + ".active{") + r"([^}]*)}", block)
    assert match
    declarations = {key.strip(): value.strip() for key, value in
                    (line.split(":", 1) for line in match.group(1).split(";") if ":" in line)}
    assert declarations["border"] == "0"
    assert declarations["box-shadow"] == "none"
    assert declarations["background"] == "transparent"
    # The legacy styling is retained for Standard and PvP.
    assert ".fight-pool.active{border-color:var(--accent);box-shadow:" in CSS
    assert '<span class="experimental-fight-versus"' in APP
    assert "experimental-fight-card-status" in APP
    assert "experimentalFightPoolHtml(fight,'attacker')" in APP
    assert "experimentalFightPoolHtml(fight,'defender')" in APP


def test_choice_panels_keep_their_interactive_framing():
    new_rule = CSS.split("/* v10.0.207: Experimental Solo Fight combatants", 1)[1]
    assert ".experimental-fight-option" not in new_rule
    assert ".experimental-fight-choice-group" not in new_rule
    assert ".fight-exchange-group" not in new_rule
    assert "experimental-fight-versus::before" in CSS
    assert 'id="confirmExperimentalFightChoice" disabled' in APP


def test_pwa_release_is_synchronized():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 207)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in HTML
    assert f'app.js?v={CURRENT_APP_VERSION}' in HTML
    assert f'styles.css?v={CURRENT_APP_VERSION}' in HTML
