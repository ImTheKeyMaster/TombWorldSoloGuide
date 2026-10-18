"""v10.0.130: combined Necron activation is standard, preview mode remains available."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_promotion_does_not_gate_necron_ui_behind_preview_toggle():
    card = APP.split("function nextStepCard(){", 1)[1].split("function missionStrategyPending()", 1)[0]
    necron = card.split("if(state.nextSide==='npo' && readyNpos().length>0){", 1)[1]
    necron = necron.split("setNextActivation(state.nextSide==='player'", 1)[0]
    assert "experimentalFeaturesEnabled()" not in necron
    assert "experimentalNecronRosterMarkup(readyNpos(),{inline:true})" in necron
    assert "skipRemainingActivationsControl()" in necron
    assert 'id="npoActivation">Resume Activation' in necron
    assert "const action=state.npoActivated>0" not in necron
    assert "if(experimentalFeaturesEnabled()&&teamName.toLowerCase()==='deathwatch')" in card


def test_standard_necron_card_has_selection_and_skip_at_all_ready_counts():
    script = r"""
const source=require('node:fs').readFileSync('app.js','utf8');
const next=source.split('function nextStepCard(){',2)[1].split('function missionStrategyPending()',1)[0];
const make=new Function('d','const {state,setNextActivation,playerOperativesRemaining,'+
  'activationSideName,experimentalFeaturesEnabled,activePlayerActivation,playerName,'+
  'experimentalDeathwatchRosterMarkup,remainingPlayerOperatives,activationProgressLabel,'+
  'escapeHtml,skipRemainingActivationsControl,activationModelLabel,readyNpos,isPvpMode,'+
  'opponentSingularLabel,experimentalNecronRosterMarkup}=d;'+
  'function nextStepCard(){'+next+'};return nextStepCard');
const check=(condition,message)=>{if(!condition)throw Error(message)};
function card(experimental,count,active=false,side='npo'){
  const state={completed:false,phase:'firefight',nextSide:side,npoActivated:0,
    playerActivated:0,activeNpoId:active?'n1':null,
    lastActivation:active?{npoId:'n1',committed:false,name:'Necron Warrior'}:null};
  return make({state,setNextActivation:()=>{},playerOperativesRemaining:()=>3,
    activationSideName:()=> 'Deathwatch',experimentalFeaturesEnabled:()=>experimental,
    activePlayerActivation:()=>null,playerName:String,
    experimentalDeathwatchRosterMarkup:()=>'<div id="experimentalInlineDeathwatchPicker"></div>',
    remainingPlayerOperatives:()=>['p1','p2','p3'],
    activationProgressLabel:()=> 'ACTIVATION 1 OF 11',escapeHtml:String,
    skipRemainingActivationsControl:()=>'<button id="skipRemainingActivations"></button>',
    activationModelLabel:()=> 'a Necron',readyNpos:()=>Array.from({length:count},
      (_,i)=>({id:'n'+i})),isPvpMode:()=>false,
    opponentSingularLabel:()=> 'Necron',
    experimentalNecronRosterMarkup:(list,options)=>
      '<section id="experimentalInlineNecronPicker">'+list.length+':'+options.inline+'</section>'
  })();
}
for(const experimental of [false,true]){
  for(const count of [1,2,8]){
    const html=card(experimental,count);
    check(html.includes(count+':true')&&html.includes('id="skipRemainingActivations"'),
      'Missing inline standard roster or skip for '+count+' ready Necrons');
    check(!html.includes('id="npoActivation"'), 'Unexpected old two-step entry button');
  }
  const resumed=card(experimental,4,true);
  check(resumed.includes('Resume Activation')&&!resumed.includes('experimentalInlineNecronPicker'),
    'An active Necron activation must resume');
}
check(card(false,2,false,'player').includes('id="playerActivation"'),
  'Standard Deathwatch activation should remain two steps');
check(card(true,2,false,'player').includes('experimentalInlineDeathwatchPicker'),
  'Experimental Deathwatch activation preview should remain available');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_standard_css_and_experimental_area_are_preserved():
    assert 'html[data-ui="tomb"] .experimental-inline-necron-card' in CSS
    assert 'html[data-experimental="on"] .experimental-inline-necron-card' not in CSS
    assert 'html[data-experimental="on"] .experimental-inline-deathwatch-card' in CSS
    assert 'id="experimentalUiToggle"' in INDEX
    assert 'data-experimental="off"' in INDEX
    assert "Preview: combine the Deathwatch activation card" in INDEX


def test_release_consistency_and_save_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 130)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
