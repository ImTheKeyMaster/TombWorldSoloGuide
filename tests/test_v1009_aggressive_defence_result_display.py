import json
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start) : APP.index(end, APP.index(start))]


def rendered_outcomes(attacker_name):
    helpers = source("function aggressiveDefenseDamage", "function aggressiveDefenseRollHtml")
    script = f"""
      const escapeHtml=value=>String(value);
      {helpers}
      console.log(JSON.stringify([1,2,3].map(roll=>aggressiveDefenseOutcome(roll,{json.dumps(attacker_name)}))));
    """
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


def test_settled_copy_uses_rule_helper_and_names_the_attacker():
    outcome = source("function aggressiveDefenseOutcome", "function aggressiveDefenseRollHtml")
    assert "aggressiveDefenseDamage(roll)" in outcome
    assert "D3 ROLL: ${roll}" in outcome
    assert "NO RETALIATORY DAMAGE" in outcome
    assert "RETALIATION" in outcome
    assert "${subject} suffers no damage." in outcome
    assert "${subject} suffers ${displayDamage} retaliatory damage." in outcome
    assert "name?escapeHtml(name):'The attacking operative'" in outcome


def test_rolls_one_two_and_three_render_the_exact_consequences():
    one, two, three = rendered_outcomes("Deathwatch Veteran Warrior")
    assert "D3 ROLL: 1" in one["html"]
    assert "NO RETALIATORY DAMAGE" in one["html"]
    assert "Deathwatch Veteran Warrior suffers no damage." in one["html"]
    for roll, outcome in ((2, two), (3, three)):
        assert f"D3 ROLL: {roll}" in outcome["html"]
        assert ">RETALIATION<" in outcome["html"]
        assert "Deathwatch Veteran Warrior suffers 1 retaliatory damage." in outcome["html"]


def test_missing_attacker_name_uses_explicit_fallback():
    one, two, _ = rendered_outcomes("")
    assert "The attacking operative suffers no damage." in one["html"]
    assert "The attacking operative suffers 1 retaliatory damage." in two["html"]
    assert one["announcement"] == "D3 Roll 1. No retaliatory damage. The attacking operative suffers no damage."


def test_rolling_hides_outcome_and_enables_continue_only_after_rendering():
    resolver = source("async function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
    assert "${animate?'':outcome.html}" in resolver
    assert "id=\"continueAggressiveDefense\" ${animate?'disabled':''}" in resolver
    assert resolver.index("result.innerHTML=outcome.html") < resolver.index("result.hidden=false")
    assert resolver.index("result.hidden=false") < resolver.index("button.disabled=false")
    assert "rollingDieHtml()" in resolver


def test_committed_roll_is_reused_for_restore_and_pvp():
    resolver = source("async function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
    assert "const restoredRoll=Number.isInteger(retaliation.roll)" in resolver
    assert "const animate=!isPvpMode()&&!restoredRoll" in resolver
    assert resolver.count("requestDiceResults(") == 1
    assert "pending.aggressiveDefenseRoll=retaliation.roll" in resolver
    assert "pending.aggressiveDefenseDamage=aggressiveDefenseDamage(retaliation.roll)" in resolver


def test_result_is_accessible_and_rendering_is_side_effect_free():
    resolver = source("async function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
    before_click = resolver.split("button.onclick=", 1)[0]
    assert 'role="status" aria-live="polite"' in before_click
    assert "result.setAttribute('aria-label',outcome.announcement)" in before_click
    assert "state.playerWounds" not in before_click
    assert "!pending.aggressiveDefenseDamageApplied" in resolver


def test_pipeline_proximity_summary_and_save_contract_are_preserved():
    pipeline = source("function applyPendingPlayerDamage", "function showReanimationProtocolsResolution")
    assert "n.type==='Canoptek Macrocyte Warrior'&&pending.attackerWithinTwo&&!pending.aggressiveDefenseResolved" in pipeline
    assert pipeline.index("showAggressiveDefenseResolution") < pipeline.index("n.wounds=Math.max")
    assert "combatAbilityReminder(combat)" in source("function renderCombatResolution", "function showSharedCombatResolutionScreen")
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (10, 0, 9)
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
