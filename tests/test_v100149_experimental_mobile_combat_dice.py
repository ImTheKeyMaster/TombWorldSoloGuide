"""Experimental mobile-only dice-first combat and animation visibility regression."""

from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
MOBILE_QUERY = "(max-width:600px), (max-width:950px) and (max-height:520px) and (orientation:landscape) and (pointer:coarse)"


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_mobile_dice_order_is_experimental_only_and_keeps_inputs_accessible():
    css = CSS.split("/* Experimental mobile Resolve Combat:", 1)[1]
    assert f"@media {MOBILE_QUERY}{{" in css
    root = 'html[data-ui="tomb"][data-experimental="on"] .combat-resolution-modal .dedicated-combat-screen > '
    for selector, order in (
        ("*", 1),
        (".compact-combat-profile", 0),
        ("#automaticCombat", 2),
        ("#combatResults", 3),
        ("#npoCombatGuidance", 4),
        ("#npoCombatRules", 4),
        (".weapon-rules", 4),
        ("#combatDetails", 5),
        (".combat-resolution-footer", 6),
    ):
        assert re.search(re.escape(root + selector) + r"\s*\{order:" + str(order) + r"\}", css), selector
    # Extra input controls (weapon picker, event checks) keep the default order 1,
    # ahead of the dice, even though their DOM nodes are after the guidance.
    screen = source("function showSharedCombatResolutionScreen(", "function showCombatResumeRecovery(")
    assert screen.index("${guidanceHtml}") < screen.index("${extraHtml}") < screen.index('id="automaticCombat"')
    assert "compact-combat-profile" in screen
    assert "modal.scrollTop=0;" in screen
    assert "modalBody.scrollTop=0;" in screen
    assert ".dedicated-combat-screen{display:grid;gap:10px}" in CSS
    # No DOM repositioning or mode-independent CSS overrides.
    assert "insertBefore(" not in screen and "appendChild(" not in screen


def test_animation_visibility_hook_is_scoped_and_runs_before_timers():
    helper = source("const EXPERIMENTAL_COMBAT_MOBILE_QUERY=", "function displaySharedCombatResult(")
    assert MOBILE_QUERY in helper
    for fragment in (
        "!experimentalFeaturesEnabled()",
        "document.documentElement.dataset.ui!=='tomb'",
        "window.matchMedia?.(EXPERIMENTAL_COMBAT_MOBILE_QUERY)?.matches",
        "!modal.open||!container?.isConnected",
        "container.querySelector('.animated-roll')",
        "roll.closest('.combat-stage')",
        "modal.scrollTop=Math.max(0,",
    ):
        assert fragment in helper

    automatic = source("function runAutomaticCombatRolls(", "function retainedDiceTotals(")
    assert automatic.count("revealExperimentalCombatDice(container)") == 2
    assert automatic.index("if(animate)revealExperimentalCombatDice(container)") < automatic.index("TombWorldDiceSfx.play()")
    assert automatic.index("revealExperimentalCombatDice(container);", automatic.index("if(showDefenseAnimation){")) < automatic.index("timer=settleCombatDice(", automatic.index("if(showDefenseAnimation){"))
    summary = source("function displaySharedCombatResult(", "function settleDimensionalBanishment(")
    assert "if(animate)revealExperimentalCombatDice(results);" in summary
    assert summary.index("revealExperimentalCombatDice(results)") < summary.index("settleCombatDice(combat")
    assert "DICE_ROLL_ANIMATION_MS" in APP


def test_scroll_helper_runtime_respects_mode_viewport_and_current_animation():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const start=app.indexOf("  const EXPERIMENTAL_COMBAT_MOBILE_QUERY=");
const end=app.indexOf("  function displaySharedCombatResult(",start);
assert(start>=0&&end>start);
const part=app.slice(start,end);
let enabled=true, mobile=true, ui='tomb';
const viewport={top:16,bottom:620};
const stage={getBoundingClientRect:()=>({top:570,bottom:720})};
const roll={closest:selector=>selector==='.combat-stage'?stage:null};
const container={isConnected:true,querySelector:selector=>selector==='.animated-roll'?roll:null};
const modal={open:true,scrollTop:0,getBoundingClientRect:()=>viewport};
const ctx={
  experimentalFeaturesEnabled:()=>enabled,
  document:{documentElement:{get dataset(){return {ui}}}},
  window:{matchMedia:query=>({matches:mobile})},
  modal
};
const reveal=new Function('ctx','with(ctx){'+part+'\nreturn revealExperimentalCombatDice;}')(ctx);
reveal(container);
assert.equal(modal.scrollTop,542,'scroll before dice animation reaches the first card');
modal.scrollTop=0;
stage.getBoundingClientRect=()=>({top:120,bottom:300});
reveal(container);
assert.equal(modal.scrollTop,0,'already-visible dice should not jump');
stage.getBoundingClientRect=()=>({top:570,bottom:720});
enabled=false;reveal(container);assert.equal(modal.scrollTop,0,'Standard UI stays untouched');
enabled=true;mobile=false;reveal(container);assert.equal(modal.scrollTop,0,'desktop stays untouched');
mobile=true;ui='classic';reveal(container);assert.equal(modal.scrollTop,0,'non-Tomb UI stays untouched');
ui='tomb';modal.open=false;reveal(container);assert.equal(modal.scrollTop,0,'closed modal stays untouched');
modal.open=true;container.isConnected=false;reveal(container);assert.equal(modal.scrollTop,0,'detached combat card stays untouched');
container.isConnected=true;container.querySelector=()=>null;reveal(container);assert.equal(modal.scrollTop,0,'static restored dice do not jump');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_standard_combat_and_version_contract_unchanged():
    screen = source("function showSharedCombatResolutionScreen(", "function showCombatResumeRecovery(")
    assert "${guidanceHtml}" in screen and "${rulesHtml}" in screen
    assert "id=\"automaticCombat\"" in screen and "id=\"combatResults\"" in screen
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    for text in ("resolveRetainedCombat", "runAutomaticCombatRolls", "settleAnimatedDice"):
        assert text in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"app.js?v={CURRENT_APP_VERSION}" in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
