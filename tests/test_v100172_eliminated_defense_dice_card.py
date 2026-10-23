"""Check promoted elimination styling targets Defense Dice in both Tomb modes."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_defense_dice_card_receives_elimination_status_in_both_tomb_modes():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
function take(start,end){
  const a=app.indexOf(start),b=app.indexOf(end,a+start.length);
  assert(a>=0&&b>a,'missing function section '+start);
  return app.slice(a,b);
}
const core=take('  function newlyEliminated(','  // Only show rules that demonstrably');
const render=take('  function renderCombatResolution(','  function combatAttackLabel(');
const stage=take('  function combatDiceStageHtml(','  function showSharedCombatResolutionScreen(');
function api(ui,experimental){
  const ctx={
    document:{documentElement:{dataset:{ui,experimental}}},
    escapeHtml:value=>String(value),
    $:selector=>{
      if(selector.endsWith('PortraitTemplate'))return {innerHTML:'<svg class="participant-portrait"></svg>'};
      if(selector==='#combatAttackerName')return {textContent:'Disruptor'};
      if(selector==='#combatDefenderName')return {textContent:'Necron Warrior 1'};
      return null;
    },
    dieHtml:die=>'<span class="die">'+die.value+'</span>',
    rollingDieHtml:()=>'<span class="rolling-die"></span>',
    severeAppliedHtml:()=>'',shootingRulesAppliedHtml:()=>'',
    combatAbilityReminder:()=>''
  };
  const extract=(source,name)=>new Function('ctx','with(ctx){'+source+'\nreturn '+name+';}')(ctx);
  Object.assign(ctx,extract(core,'{newlyEliminated,renderEliminationSummary}'));
  ctx.combatDiceStageHtml=extract(stage,'combatDiceStageHtml');
  return extract(render,'renderCombatResolution');
}
const wounded={
 before:1,after:0,damage:4,normalRemaining:0,critRemaining:1,
 attackerName:'Disruptor',defenderName:'Necron Warrior 1',defenderSide:'npo',
 attackType:'shoot',recordedOutcome:false,attackDice:[{value:6}],saveDice:[{value:3}],
 profile:{},eventMessages:[],coverRetained:false
};
function extractStage(html,label){
  const stage=html.match(new RegExp('<section class="([^"]+)" aria-label="'+label+'[^"]*">([\\s\\S]*?)<\\/section>'));
  assert(stage,'missing '+label+' stage');
  return {classes:stage[1],html:stage[0]};
}
const exp=api('tomb','on'),standard=api('tomb','off'),classic=api('classic','on');
for(const render of [exp,standard]){
for(const type of ['shoot','melee']){
  const output=render({...wounded,attackType:type},{animate:false,showParticipants:false});
  const attacker=extractStage(output,'ATTACK DICE');
  const defender=extractStage(output,'DEFENSE DICE');
  assert.match(output,/^<section class="combat-resolution" aria-label="Combat resolution">/,
    'outer combat resolution must have no elimination class');
  assert.doesNotMatch(attacker.classes,/experimental-eliminated-card/);
  assert.doesNotMatch(attacker.html,/ELIMINATED/);
  assert.match(defender.classes,/experimental-eliminated-card/);
  assert.match(defender.html,/aria-label="DEFENSE DICE for Necron Warrior 1, eliminated"/);
  assert.match(defender.html,/<strong class="experimental-eliminated-label">ELIMINATED<\/strong><\/section>/);
  assert.match(defender.html,/class="participant-portrait"/,'preserve defender artwork');
  assert.match(defender.html,/class="die"/,'preserve rolled defense dice');
  assert.doesNotMatch(output,/elimination-banner|eliminated-badge/);
  assert.equal((output.match(/>ELIMINATED<\/strong>/g)||[]).length,1);
  assert.match(output,/Wounds/,'preserve damage and wounds');
}}
const animated=exp(wounded,{animate:true});
assert.match(extractStage(animated,'DEFENSE DICE').html,/animated-roll/);
assert.match(extractStage(animated,'DEFENSE DICE').classes,/experimental-eliminated-card/);
assert.match(extractStage(standard(wounded,{animate:true}),'DEFENSE DICE').classes,/experimental-eliminated-card/);
for(const output of [
 exp({...wounded,before:3,after:1},{animate:false}),
 exp({...wounded,before:0,after:0},{animate:false}),
 standard({...wounded,before:3,after:1},{animate:false}),
 standard({...wounded,before:0,after:0},{animate:false})
]){
  assert.doesNotMatch(output,/experimental-eliminated-card|experimental-eliminated-label/);
  assert.doesNotMatch(extractStage(output,'DEFENSE DICE').html,/ELIMINATED/);
}
for(const render of [classic]){
  const output=render(wounded,{animate:false});
  assert.match(output,/elimination-banner/,'previous mode must retain its banner');
  assert.doesNotMatch(output,/experimental-eliminated-card|experimental-eliminated-label/);
  assert.doesNotMatch(extractStage(output,'DEFENSE DICE').html,/ELIMINATED/);
}
const tabletop=exp({...wounded,recordedOutcome:true},{animate:false});
assert.match(tabletop,/TABLETOP RESOLUTION/);
assert.doesNotMatch(tabletop,/experimental-eliminated-card/);
assert.match(tabletop,/>ELIMINATED<\/strong>/,'manual tabletop results still announce elimination');
assert.equal(standard({...wounded,recordedOutcome:true},{animate:false}),tabletop,
 'recorded tabletop elimination is the same in Standard and Experimental');
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, timeout=30
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_scoped_css_and_unmodified_legacy_elimination_surfaces():
    preview = CSS.split("/* v10.0.171/173: Approved text-first", 1)[1]
    assert 'html[data-ui="tomb"] .combat-stage.experimental-eliminated-card' in preview
    assert '[data-experimental="on"]' not in preview
    assert '.combat-resolution.experimental-eliminated-card' not in preview
    assert "border:2px solid var(--danger,#ef6b6b)" in preview
    assert 'background:rgba(125,25,25,.2)' not in preview
    assert 'html[data-ui="tomb"] .experimental-eliminated-card .experimental-eliminated-label' in preview
    assert '.fight-result-card.experimental-eliminated-card' in preview
    assert '.attack-confirmation-card.experimental-eliminated-card' in preview
    assert "background:rgba(0,0,0,.18)" in CSS
    assert ".elimination-banner{" in CSS


def test_release_and_save_format_stay_compatible():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert f'styles.css?v={CURRENT_APP_VERSION}' in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
