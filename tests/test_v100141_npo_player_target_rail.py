"""Runtime regression coverage for Necron attack target rails on both player teams."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_attack_target_rail_renders_both_teams_and_selected_state():
    run_node(r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const section=(start,end)=>{
  const a=src.indexOf(start),b=src.indexOf(end,a+start.length);
  assert(a>=0&&b>a,'Missing '+start);
  return src.slice(a,b);
};
const code=[
  section('  const DEATH_KORPS_PORTRAIT_ROOT=', '  // Warm once per unique photograph'),
  section('  function playerRosterPortraitMarkup(', '  function usesPlayerPortraitRail('),
  section('  function experimentalNpoTargetRosterRail(', '  function updateNpoTargetConfirmationAvailability(')
].join('\n');
for(const team of ['Deathwatch','Death Korps']){
  const state={npoAttackTargetId:'confidant'};
  const context={
    state,selectedPlayerTeamName:()=>team,
    experimentalDeathwatchGreenPortraitSvg:id=>'<svg data-deathwatch="'+id+'"></svg>',
    playerCurrentWounds:id=>id==='confidant'?4:7,
    playerDefinition:id=>({wounds:9}),
    playerName:id=>id==='confidant'?'Confidant':'Gunner (Flamer)',
    playerTargetAriaLabel:id=>'Target '+id,
    escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')
  };
  const make=new Function('context','with(context){'+code+'\nreturn experimentalNpoTargetRosterRail;}')(context);
  const html=make(['confidant','gunner-flamer']);
  assert.match(html,/role="radiogroup"/);
  assert.equal((html.match(/role="radio"/g)||[]).length,2);
  assert.match(html,/data-npo-target-id="confidant"/);
  assert.match(html,/aria-checked="true"/);
  assert.match(html,/aria-checked="false"/);
  assert.match(html,/4\/9 wounds/);
  assert.match(html,/7\/9 wounds/);
  if(team==='Death Korps'){
    assert.match(html,/Death_Korps_confidant\.png/);
    assert.match(html,/Death_Korps_gunner\.png/);
    assert.doesNotMatch(html,/data-deathwatch=/);
  }else{
    assert.match(html,/data-deathwatch="confidant"/);
    assert.match(html,/data-deathwatch="gunner-flamer"/);
    assert.doesNotMatch(html,/Death_Korps_/);
  }
  state.npoAttackTargetId='';
  const empty=make(['confidant','gunner-flamer']);
  assert.equal((empty.match(/aria-checked="true"/g)||[]).length,0);
  assert.match(empty,/tabindex="0"/);
}
""");


def test_target_confirmation_accepts_valid_and_rejects_stale_choices():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const a=src.indexOf('  function confirmNpoAttackTarget(n,decision){');
const b=src.indexOf('  function openNpoCombat(',a);
assert(a>=0&&b>a);
const code=src.slice(a,b);
for(const valid of [true,false]){
  const events=[];
  const state={
    npoAttackTargetId:'confidant',npoAttackSummary:null,
    lastActivation:{pendingAction:{id:'shoot'},answers:{},targetConfirmed:false},
    activationHistory:[]
  };
  const ctx={state,
    $:()=>null,eligibleNpoAttackTargets:()=>valid?['confidant']:['gunner-flamer'],
    renderNpoDecisionResult:()=>events.push('rerender'),
    showToast:()=>events.push('toast'),
    save:()=>events.push('save'),
    openNpoCombat:()=>events.push('combat'),
    playerSideLabel:()=> 'Death Korps',
    log:()=>events.push('log'),
    npoName:()=> 'Canoptek Tomb Crawler',
    playerName:()=> 'Confidant',
    showNpoTargetRecovery:()=>events.push('recovery')
  };
  const confirm=new Function('ctx','with(ctx){'+code+'\nreturn confirmNpoAttackTarget;}')(ctx);
  const result=confirm({id:'crawler'}, {action:'Shoot'});
  assert.equal(result,valid);
  if(valid){
    assert.equal(state.npoAttackTargetId,'confidant');
    assert.equal(state.lastActivation.targetConfirmed,true);
    assert.deepEqual(events.filter(e=>e==='combat'),['combat']);
    assert(!events.includes('rerender'));
  }else{
    assert.equal(state.npoAttackTargetId,null);
    assert(!events.includes('combat'));
    assert(events.includes('rerender')&&events.includes('toast'));
  }
}
""");


def test_target_rail_is_team_aware_and_retains_selection_navigation():
    section = APP.split("function renderNpoDecisionResult(", 1)[1].split(
        "async function completeNpoActivation", 1
    )[0]
    helper = APP.split("function experimentalNpoTargetRosterRail(", 1)[1].split(
        "function updateNpoTargetConfirmationAvailability", 1
    )[0]
    assert "usesPlayerPortraitRail()&&attackRequired&&!targetConfirmed&&eligibleTargetIds.length>0" in section
    assert "playerRosterPortraitMarkup(id," in helper
    assert "experimentalNpoTargetRosterRail(eligibleTargetIds)" in section
    assert "const targetButtons=$$('[data-npo-target-id]',modal);" in section
    for expression in (
        "state.npoAttackTargetId=id;",
        "updateNpoTargetConfirmationAvailability();",
        "['ArrowLeft','ArrowRight','Home','End']",
        "nextButton.scrollIntoView({block:'nearest',inline:'nearest'})",
        "if(!eligibleNpoAttackTargets().includes(id))",
        "aria-checked",
    ):
        assert expression in section or expression in helper


def test_portrait_rail_responsive_and_release_consistent():
    assert "html[data-ui=\"tomb\"] .npo-target-roster-rail{overflow-x:auto" in CSS
    assert "html[data-ui=\"tomb\"] .npo-target-roster-wounds" in CSS
    assert "V" + CURRENT_APP_VERSION in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
