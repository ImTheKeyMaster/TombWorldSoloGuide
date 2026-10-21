"""Experimental-only compact Sweeping target count above animated dice."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_sweeping_compact_label_runtime_and_standard_full_details():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const source=(a,b)=>app.slice(app.indexOf('  '+a),app.indexOf('  '+b,app.indexOf('  '+a)));
const progress=source('function experimentalSweepingTargetProgress(', 'function showMultiTargetAttackSummary(');
const shared=source('function showSharedCombatResolutionScreen(', 'function showCombatResumeRecovery(');
let enabled=true,ui='tomb',markup='',scrolls=0;
const ctx={
  experimentalFeaturesEnabled:()=>enabled,
  document:{documentElement:{get dataset(){return {ui}}}},
  escapeHtml:value=>String(value),
  showModal:(title,html)=>{markup=html},
  modal:{classList:{add:()=>{}},scrollTop:0},
  modalBody:{scrollTop:0},
  window:{scrollTo:()=>scrolls++},
  $:selector=>({selector})
};
const api=new Function('ctx','with(ctx){'+progress+shared+
  '\nreturn {experimentalSweepingTargetProgress,weaponRuleSequenceProgress,showSharedCombatResolutionScreen};}')(ctx);
const sequence={ruleId:'torrent',profileKey:'sweeping',weaponName:'Twin gauss reapers',currentSequenceIndex:1,totalSequences:3};
const label=api.experimentalSweepingTargetProgress(sequence);
assert.match(label,/^<p class="experimental-sweeping-progress" aria-live="polite">Target 2 of 3<\/p>$/);
assert.doesNotMatch(label,/Sweeping|Twin gauss|Gunner|wounds|ATTACK/);
assert.match(api.experimentalSweepingTargetProgress({...sequence,currentSequenceIndex:0}),/Target 1 of 3/);
assert.match(api.experimentalSweepingTargetProgress({...sequence,currentSequenceIndex:2}),/Target 3 of 3/);
const fresh={ruleId:'torrent',profileKey:'sweeping',orderedTargetIds:['sergeant','gunner','blademaster'],currentSequenceIndex:0};
assert.match(api.experimentalSweepingTargetProgress(fresh),/Target 1 of 3/,'freshly selected secondary targets have no totalSequences yet');
assert.match(api.experimentalSweepingTargetProgress({...fresh,currentSequenceIndex:1}),/Target 2 of 3/);
assert.equal(api.experimentalSweepingTargetProgress({...fresh,orderedTargetIds:['sergeant']}),'','single-target Sweeping must not show the counter');
assert.equal(api.experimentalSweepingTargetProgress({...fresh,orderedTargetIds:[]}),'' ,'empty target list must not show a counter');
assert.equal(api.experimentalSweepingTargetProgress({...fresh,orderedTargetIds:null,totalSequences:3}),api.experimentalSweepingTargetProgress({...fresh,totalSequences:3}));
assert.equal(api.experimentalSweepingTargetProgress({...sequence,totalSequences:1}),'');
assert.equal(api.experimentalSweepingTargetProgress({...sequence,profileKey:'focused'}),'');
assert.equal(api.experimentalSweepingTargetProgress({...sequence,profileKey:'blast',ruleId:'blast'}),'');
assert.equal(api.experimentalSweepingTargetProgress(null),'');
const full=api.weaponRuleSequenceProgress(sequence,'Gunner','2/15 wounds');
assert.match(full,/SWEEPING ATTACK/);
assert.match(full,/Twin gauss reapers/);
assert.match(full,/Target 2 of 3/);
assert.match(full,/Gunner \(2\/15 wounds\)/);
api.showSharedCombatResolutionScreen({
  title:'Resolve Combat',attackerName:'Canoptek Tomb Crawler 2',defenderName:'Gunner',
  attackType:'shoot',weaponName:'Twin gauss reapers: Sweeping',attackLabel:'4 dice · 4+',
  defenseLabel:'3 dice · 3+',cancelId:'cancel',continueId:'continue',
  progressHtml:label,detailsHtml:'',rulesHtml:'<div id="rules">Piercing 1</div>'
});
assert(markup.indexOf('id="rules"')<markup.indexOf('Target 2 of 3'));
assert(markup.indexOf('Target 2 of 3')<markup.indexOf('id="automaticCombat"'));
assert(markup.indexOf('id="automaticCombat"')<markup.indexOf('id="combatResults"'));
assert(markup.indexOf('id="combatResults"')<markup.indexOf('id="combatDetails"'));
assert.match(markup,/<div id="combatDetails"><\/div>/);
assert.doesNotMatch(markup,/SWEEPING ATTACK|Target 2 of 3<br>|Gunner \(2\/15 wounds\)/);
assert.equal(scrolls,1);
enabled=false;
assert.equal(api.experimentalSweepingTargetProgress(sequence),label,'Standard Tomb UI shows compact Sweeping progress too');
api.showSharedCombatResolutionScreen({
  title:'Resolve Combat',attackerName:'Crawler',defenderName:'Gunner',
  attackType:'shoot',weaponName:'Sweeping',defenseLabel:'3 dice · 3+',
  cancelId:'cancel',continueId:'continue',detailsHtml:full
});
assert.match(markup,/SWEEPING ATTACK/);
assert.match(markup,/Gunner \(2\/15 wounds\)/);
assert(markup.indexOf('id="automaticCombat"')<markup.indexOf('SWEEPING ATTACK'));
enabled=true;ui='classic';
assert.equal(api.experimentalSweepingTargetProgress(sequence),'');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_both_player_and_npo_flows_use_existing_sequence_without_changing_mechanics():
    player = source("  function showPlayerCombatResolution(", "  async function previewPendingPlayerAttack(")
    npo = source("  function showNpoAttackWizard(", "  function spinnerField(")
    for wizard in (player, npo):
        assert "progressHtml:experimentalSweepingTargetProgress(sequence)," in wizard
        assert "detailsHtml:experimentalSweepingTargetProgress(sequence)?'':weaponRuleSequenceProgress(sequence," in wizard
        assert "showSharedCombatResolutionScreen({" in wizard
    assert "progressHtml=''" in source("  function showSharedCombatResolutionScreen(", "  function showCombatResumeRecovery(")
    assert "renderCombatResolution(" in APP
    assert "runAutomaticCombatRolls(" in APP
    assert "createWeaponRuleResolution(" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_mobile_order_and_green_label_are_experiment_scoped():
    rules = CSS.split("/* Experimental Sweeping: show only", 1)[1]
    assert 'html[data-ui="tomb"] .combat-resolution-modal .experimental-sweeping-progress{' in rules
    assert "color:var(--green);" in rules
    assert "font-weight:850;" in rules
    assert ".experimental-sweeping-progress ~ #combatDetails:empty{display:none}" in rules
    assert ".dedicated-combat-screen > .experimental-sweeping-progress{order:2}" in rules
    assert "(max-width:600px)" in rules
    assert "(orientation:landscape) and (pointer:coarse)" in rules
    assert ".dedicated-combat-screen > #automaticCombat{order:2}" in CSS
    assert ".dedicated-combat-screen > #combatResults{order:3}" in CSS


def test_version_references():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"app.js?v={CURRENT_APP_VERSION}" in INDEX


def test_animation_auto_scroll_keeps_counter_visible_above_attack_dice():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const start=app.indexOf("  const EXPERIMENTAL_COMBAT_MOBILE_QUERY=");
const end=app.indexOf("  function displaySharedCombatResult(",start);
assert(start>0&&end>start);
const part=app.slice(start,end);
let ui='tomb',enabled=true,mobile=true;
const viewport={top:16,bottom:620};
const progress={getBoundingClientRect:()=>({top:536,bottom:557})};
let currentStage='attack';
const attackStage={getBoundingClientRect:()=>({top:570,bottom:720})};
const defenseStage={getBoundingClientRect:()=>({top:730,bottom:880})};
const roll={closest:selector=>selector==='.combat-stage'?(currentStage==='attack'?attackStage:defenseStage):null};
const screen={querySelector:selector=>selector==='.experimental-sweeping-progress'?progress:null};
const container={
  isConnected:true,
  querySelector:selector=>selector==='.animated-roll'?roll:selector==='.combat-stage'?attackStage:null,
  closest:selector=>selector==='.dedicated-combat-screen'?screen:null
};
const modal={open:true,scrollTop:0,getBoundingClientRect:()=>viewport};
const ctx={experimentalFeaturesEnabled:()=>enabled,document:{documentElement:{get dataset(){return {ui}}}},
  window:{matchMedia:()=>({matches:mobile})},modal};
const reveal=new Function('ctx','with(ctx){'+part+'\nreturn revealExperimentalCombatDice;}')(ctx);
reveal(container);
assert.equal(modal.scrollTop,508,'first attack should scroll to the green counter, not past it');
modal.scrollTop=0;
currentStage='defense';
reveal(container);
assert.equal(modal.scrollTop,702,'defense animation should still scroll to the active defense card');
modal.scrollTop=0;
currentStage='attack';
progress.getBoundingClientRect=()=>({top:180,bottom:201});
attackStage.getBoundingClientRect=()=>({top:214,bottom:370});
reveal(container);
assert.equal(modal.scrollTop,0,'already visible progress and dice do not jump');
modal.scrollTop=0;enabled=false;
progress.getBoundingClientRect=()=>({top:536,bottom:557});
attackStage.getBoundingClientRect=()=>({top:570,bottom:720});
reveal(container);
assert.equal(modal.scrollTop,508,'Standard Tomb UI also keeps Sweeping progress visible');
modal.scrollTop=0;
enabled=true;mobile=false;
reveal(container);
assert.equal(modal.scrollTop,0,'desktop remains untouched');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
