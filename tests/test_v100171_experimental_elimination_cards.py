"""Shared Standard and Experimental elimination card regressions."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_eliminations_have_consistent_promoted_markup_without_affecting_classic():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
function slice(start,end){
  const a=app.indexOf(start),b=app.indexOf(end,a+start.length);
  assert(a>=0&&b>a,start);
  return app.slice(a,b);
}
const core=slice('  function newlyEliminated(','  // Only show rules that demonstrably');
const combatCode=slice('  function renderCombatResolution(','  function combatAttackLabel(');
const fightCode=slice('  function fightResultParticipantHtml(','  function acknowledgeFightResult(');
const make=(code,name,ctx)=>new Function('ctx',
  'with(ctx){'+code+'\nreturn '+name+';}')(ctx);
const target={
  before:1,after:0,damage:2,normalRemaining:1,critRemaining:0,
  side:'npo',defenderSide:'npo',
  targetName:'Canoptek Scarab Swarm 2',defenderName:'Canoptek Scarab Swarm 2',
  attackerName:'Canoptek Macrocyte Warrior 1',
  attackType:'shoot',recordedOutcome:true,attackDice:[],saveDice:[],
  profile:{},eventMessages:[]
};
function useMode(ui,experimental){
  const ctx={
    document:{documentElement:{dataset:{ui,experimental}}},
    escapeHtml:x=>String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;'),
    shootingRulesAppliedHtml:()=>'',combatAbilityReminder:()=>'',
    fightParticipantPortrait:()=>'',combatDiceStageHtml:()=>''
  };
  const coreApi=make(core,
    '{newlyEliminated,renderEliminationSummary,renderAttackSummary}',ctx);
  Object.assign(ctx,coreApi);
  return {
    core:coreApi,
    combat:make(combatCode,'renderCombatResolution',ctx),
    fight:make(fightCode,'fightResultParticipantHtml',ctx)
  };
}
const experiment=useMode('tomb','on');
const standard=useMode('tomb','off');
const classic=useMode('classic','on');
const dying={name:'Canoptek Scarab Swarm 3',before:10,after:0,damageDealt:1,incapacitated:true};
const surviving={...dying,after:6,incapacitated:false};

for(const output of [
  experiment.fight(dying,'attacker'),
  experiment.fight(dying,'defender'),
  standard.fight(dying,'attacker'),
  standard.fight(dying,'defender'),
  experiment.core.renderAttackSummary(target,{portraitHtml:'<span class="blast-result-portrait"></span>'}),
  standard.core.renderAttackSummary(target,{portraitHtml:'<span class="blast-result-portrait"></span>'})
]){
  assert.match(output,/experimental-eliminated-card/);
  assert.match(output,/>ELIMINATED<\/strong>/);
}
const fight=experiment.fight(dying,'defender');
assert.match(fight,/class="fight-eliminated">ELIMINATED<\/strong>/);
assert.match(fight,/Wounds/);
const combat=experiment.combat(target,{animate:false});
assert.doesNotMatch(combat,/elimination-banner|eliminated-badge|experimental-eliminated-card/);
assert.match(combat,/experimental-eliminated-label/);
assert.match(combat,/Wounds/);
assert.match(combat,/1 → 0/);
assert.equal(experiment.core.renderEliminationSummary(target),'');
assert.equal(standard.core.renderEliminationSummary(target),'');
assert.equal(standard.combat(target,{animate:false}),combat,'Standard and Experimental share the recorded-result fallback');
const summary=experiment.core.renderAttackSummary(target,{portraitHtml:'<span class="blast-result-portrait"></span>'});
assert.doesNotMatch(summary,/eliminated-badge|☠/);
assert.match(summary,/blast-result-portrait/);
assert.match(summary,/class="attack-confirmation-stats"/);

for(const promoted of [standard,experiment]){
  const attack=promoted.core.renderAttackSummary(target);
  assert.match(attack,/experimental-eliminated-card/);
  assert.match(attack,/experimental-eliminated-label/);
  assert.doesNotMatch(attack,/eliminated-badge|☠/);
  assert.match(promoted.fight(dying,'attacker'),/experimental-eliminated-card/);
  assert.match(promoted.fight(dying,'defender'),/experimental-eliminated-card/);
  assert.doesNotMatch(promoted.combat(target,{animate:false}),/elimination-banner/);
  assert.match(promoted.combat(target,{animate:false}),/experimental-eliminated-label/);
  assert.equal(promoted.core.renderEliminationSummary(target),'');
}
assert.doesNotMatch(classic.fight(dying,'attacker'),/experimental-eliminated-card/);
assert.match(classic.fight(dying,'attacker'),/class="fight-eliminated">ELIMINATED/);
assert.match(classic.combat(target,{animate:false}),/elimination-banner/);
assert.match(classic.core.renderAttackSummary(target),/eliminated-badge/);
assert.doesNotMatch(classic.core.renderAttackSummary(target),/experimental-eliminated-label/);
assert.doesNotMatch(experiment.fight(surviving,'attacker'),/experimental-eliminated-card|fight-eliminated/);
assert.doesNotMatch(standard.fight(surviving,'attacker'),/experimental-eliminated-card|fight-eliminated/);
assert.doesNotMatch(experiment.combat({...target,before:3,after:1},{animate:false}),/experimental-eliminated-card|experimental-eliminated-label/);
assert.doesNotMatch(experiment.core.renderAttackSummary({...target,before:3,after:1}),/experimental-eliminated-card|experimental-eliminated-label/);
"""
    run = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert run.returncode == 0, run.stderr or run.stdout


def test_promoted_css_is_shared_and_keeps_default_dark_background():
    preview = CSS.split("/* v10.0.171/173: Approved text-first", 1)[1]
    assert 'html[data-ui="tomb"]' in preview
    assert '[data-experimental="on"]' not in preview
    assert '.fight-result-card.experimental-eliminated-card' in preview
    assert '.combat-stage.experimental-eliminated-card' in preview
    assert '.attack-confirmation-card.experimental-eliminated-card' in preview
    assert "border:2px solid var(--danger,#ef6b6b)" in preview
    assert "background:rgba(16,51,34,.45)" in preview
    assert ".combat-resolution.experimental-eliminated-card" not in preview
    assert "font-size:1.08rem" in preview
    assert 'background:rgba(125,25,25,.2)' not in preview
    # Classic's legacy banner and badge remain available; Tomb overrides the fill.
    assert ".elimination-banner{" in CSS
    assert ".eliminated-badge{" in CSS
    assert ".attack-confirmation-card.eliminated{" in CSS


def test_release_and_persistence_unchanged():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in html
    assert f"styles.css?v={CURRENT_APP_VERSION}" in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
