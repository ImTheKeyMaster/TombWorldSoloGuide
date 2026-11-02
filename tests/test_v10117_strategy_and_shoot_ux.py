"""Regression tests for paused Strategy recovery and second-Shoot AP feedback."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def body(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def node(source):
    return subprocess.run(
        ["node", "-e", source], cwd=ROOT, check=True,
        capture_output=True, text=True,
    )


def test_paused_strategy_copy_is_actionable_and_does_not_claim_lost_dice():
    card = body("function strategyCard", "function strategyEventHtml")
    assert "<h2>Resume Strategy Phase</h2>" in card
    assert "Dice results already recorded will not be rerolled." in card
    assert 'id="retryStrategyDice"' in card
    assert "Dice resolution interrupted" not in card
    assert "finishTurningPointStart" in body("function bindPlay", "async function startTurningPoint")


def test_experimental_reinforcement_card_follows_stable_checkbox_list():
    review = body("function strategyReviewStepHtml", "function reinforcementBlockedReason")
    assert "const placementChecklist=deployingNpos.length?" in review
    assert "experimentalFeaturesEnabled()?\u0060\u0024{placementChecklist}\u0024{reinforcementCard}\u0060:\u0060\u0024{reinforcementCard}\u0024{placementChecklist}\u0060" in review
    assert "\u0024{warning}\u0024{reinforcementContent}\u0024{battlefield}" in review
    assert "npo.reinforcement?.placementConfirmed" in review
    assert 'data-reinforcement-placement=' in review


def test_legal_and_illegal_second_shoots_follow_original_rules():
    funcs = body("function playerActionUses", "function spectreFieldcraftRecord")
    action = body("function playerHumanActionState", "function renderHumanActivationShell")
    node(f"""
      const assert=require('node:assert/strict');
      const isDeathwatchPlayerTeam=()=>true;
      const playerAttackWeapons=()=>[
        {{type:'ranged',name:'Plasma pistol (standard)'}},
        {{type:'ranged',name:'Plasma pistol (supercharge)'}}
      ];
      const hasValidPlayerCombatTargets=()=>true;
      {funcs}
      {action}
      const activation=remainingAp=>({{
        operativeId:'sergeant',remainingAp,completedActionIds:['shoot'],
        resolvedActions:[{{id:'shoot',attackSummaries:[{{weaponName:'Plasma pistol (standard)'}}]}}]
      }});
      assert.equal(deathwatchSecondShootExtraCost(activation(1),'Plasma pistol (supercharge)'),1);
      const blocked=playerHumanActionState({{id:'shoot',cost:1}},activation(1));
      assert.equal(blocked.disabled,true);
      assert.equal(blocked.reason,'Second Shoot requires 2 AP');
      const legal=playerHumanActionState({{id:'shoot',cost:1}},activation(2));
      assert.equal(legal.disabled,false);
      assert.equal(legal.status,'Available');
    """)


def test_weapon_screen_explains_why_continue_is_disabled():
    wizard = body("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
    assert 'id="playerShootApGuidance" role="status" aria-live="polite"' in wizard
    assert "const requiredAp=1+extraAp;" in wizard
    assert "remainingAp<requiredAp" in wizard
    assert "apGuidance.hidden=!insufficientAp;" in wizard
    assert "Cancel and choose another action." in wizard
    assert "weaponSelect.addEventListener('change',renderChoices)" in wizard
    assert "$('#openCombatResolution').disabled=!target||!weapon||insufficientAp;" in wizard
    assert "if(activePlayerActivation().remainingAp<required)" in wizard
    assert ".combat-ap-guidance:not([hidden])" in CSS


def test_unchanged_strategy_and_ap_commit_paths():
    assert "npo.reinforcement.placementConfirmed=Boolean(confirmed);" in APP
    assert "pending.cost=required;stage.humanActionCost=required;save();" in APP
    assert "acknowledgeDiceRequest(requestKey)" in APP
    assert "canLeaveStrategyEvents()" in APP

def test_reinforcement_placement_bindings_work_with_zero_or_multiple_rows():
    """The resumed game must render even when no new reinforcements are pending."""
    bind = body("function bindPlay(){", "let skipRemainingActivationsPending")
    line = next(line.strip() for line in bind.splitlines()
                if "data-reinforcement-placement" in line)
    assert line.startswith("$$('[data-reinforcement-placement]').forEach(")
    node(f"""
      const assert=require('node:assert/strict');
      let elements=[];
      let confirmations=[];
      const $$=()=>elements;
      const confirmReinforcementPlacement=(id,confirmed)=>confirmations.push([id,confirmed]);
      // A saved game without pending reinforcements previously crashed on startup.
      {line}
      assert.deepEqual(confirmations,[]);
      const checkbox=(id,checked)=>({{
        dataset:{{reinforcementPlacement:id}},checked,
        addEventListener(type,fn){{assert.equal(type,'change');this.onChange=fn;}}
      }});
      elements=[checkbox('npo-1',true),checkbox('npo-2',false)];
      {line}
      assert.equal(typeof elements[0].onChange,'function');
      assert.equal(typeof elements[1].onChange,'function');
      elements[0].onChange();
      elements[1].onChange();
      assert.deepEqual(confirmations,[['npo-1',true],['npo-2',false]]);
    """)
