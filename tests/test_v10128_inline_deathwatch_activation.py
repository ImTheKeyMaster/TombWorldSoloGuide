"""Experimental-only inline Deathwatch activation without changing Standard mode."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def run_js(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_card_modes_and_existing_activation_paths():
    run_js(r"""
const fs=require('node:fs'),source=fs.readFileSync('app.js','utf8');
const block=(begin,end)=>source.slice(source.indexOf(begin),source.indexOf(end,source.indexOf(begin)));
const body=block('function nextStepCard(){','function missionStrategyPending()');
const create=new Function('ctx',`
const {state,setNextActivation,playerOperativesRemaining,activationSideName,
experimentalFeaturesEnabled,activePlayerActivation,playerName,
experimentalDeathwatchRosterMarkup,remainingPlayerOperatives,activationProgressLabel,
escapeHtml,skipRemainingActivationsControl,activationModelLabel,readyNpos,
isPvpMode,opponentSingularLabel}=ctx;
${body};
return nextStepCard;
`);
function card({experimental=false,team='Deathwatch',side='player',active=null,count=4}={}){
  const state={completed:false,phase:'firefight',nextSide:side,playerActivated:1,
    npoActivated:1,initiative:'player'};
  return create({state,setNextActivation:()=>{},playerOperativesRemaining:()=>count,
    activationSideName:x=>x==='player'?team:'Necron',
    experimentalFeaturesEnabled:()=>experimental,activePlayerActivation:()=>active,
    playerName:id=>id,
    experimentalDeathwatchRosterMarkup:(ids,options)=>`<div id="experimentalInlineDeathwatchPicker">ROSTER ${ids.length},${options.inline}</div>`,
    remainingPlayerOperatives:()=>Array.from({length:count},(_,i)=>String(i)),
    activationProgressLabel:()=> 'ACTIVATION 2 OF 13',escapeHtml:String,
    skipRemainingActivationsControl:()=>'<button id="skipRemainingActivations">Skip Remaining</button>',
    activationModelLabel:()=> 'a Deathwatch Operative',readyNpos:()=>[{id:'n1'}],
    isPvpMode:()=>false,opponentSingularLabel:()=> 'Necron'
  })();
}
const check=(x,message)=>{if(!x)throw Error(message);};
const standard=card();
check(standard.includes('id="playerActivation"')&&!standard.includes('experimentalInlineDeathwatchPicker'),
  'Standard mode no longer shows its existing activation button');
const inline=card({experimental:true});
check(inline.includes('ROSTER 4,true')&&inline.includes('id="skipRemainingActivations"')&&
  !inline.includes('id="playerActivation"'), 'Experimental Deathwatch card not consolidated');
check(card({experimental:true,count:1}).includes('ROSTER 1,true'), 'Single remaining operative excluded');
const resumed=card({experimental:true,active:{operativeId:'disruptor'}});
check(resumed.includes('Resume Activation')&&!resumed.includes('experimentalInlineDeathwatchPicker'),
  'An unfinished activation must resume, not start again');
check(card({experimental:true,team:'Kasrkin'}).includes('id="playerActivation"'),
  'Other Kill Teams changed');
const necron=card({experimental:true,side:'npo'});
check(necron.includes('id="npoActivation"')&&!necron.includes('experimentalInlineDeathwatchPicker'),
  'Necron screen changed');
""")


def test_shared_rail_in_inline_and_modal_modes_with_keyboard_selection():
    run_js(r"""
const fs=require('node:fs'),source=fs.readFileSync('app.js','utf8');
const block=(begin,end)=>source.slice(source.indexOf(begin),source.indexOf(end,source.indexOf(begin)));
const markup=block('function experimentalDeathwatchRosterMarkup(', 'function showExperimentalDeathwatchRosterRail(');
const binding=block('function bindExperimentalDeathwatchRosterRail(', 'function showPlayerActivation()');
const check=(x,message)=>{if(!x)throw Error(message);};
const createMarkup=new Function('warmDeathwatchRosterImages','escapeHtml',
  'experimentalDeathwatchGreenPortraitSvg','playerName',markup+
  ';return experimentalDeathwatchRosterMarkup');
const mk=createMarkup(()=>{},String,id=>'<svg>'+id+'</svg>',id=>id);
const inline=mk(['breacher','demolisher'],{inline:true});
const modal=mk(['breacher','demolisher']);
check(inline.includes('id="experimentalInlineDeathwatchPicker"')&&
  inline.includes('id="confirmExperimentalRosterSelection" disabled')&&
  !inline.includes('data-close>Close Guide'), 'Wrong inline roster actions');
check(modal.includes('data-close>Close Guide')&&
  !modal.includes('experimentalInlineDeathwatchPicker'), 'Existing modal markup changed');

const classes=()=>({add:()=>{},remove:()=>{},toggle:()=>{}});
let focused=null,begun=null;
const buttons=['breacher','demolisher'].map(id=>({
  dataset:{rosterOperative:id},classList:classes(),tabIndex:0,
  querySelector:()=>({scrollHeight:10}),setAttribute(k,v){this[k]=v;},
  focus(){focused=this}
}));
const names=['#confirmExperimentalRosterSelection','#experimentalRosterDetailImage',
  '#experimentalRosterDetailName','#experimentalRosterDetailRole','#experimentalRosterStats'];
const elements=Object.fromEntries(names.map(x=>[x,{
  disabled:true,classList:classes(),removeAttribute:()=>{},innerHTML:'',textContent:''
}]));
const root={querySelector:key=>elements[key],querySelectorAll:key=>
  key==='[data-roster-operative]'?buttons:[]};
const env=new Function('root','buttons','elements','focused','begin',binding+`
const $=(selector,scope)=>scope.querySelector(selector);
`); // Binder's dependencies are injected below, not via this unused factory.
const bind=new Function('deps',`
const {$$,$,requestAnimationFrame,getComputedStyle,livePlayerOperative,playerDefinition,
 effectiveApl,playerCurrentWounds,experimentalDeathwatchGreenPortraitSvg,
 playerName,escapeHtml,beginPlayerActivation}=deps;
${binding}
return bindExperimentalDeathwatchRosterRail;
`)({
  $$:(selector,scope)=>[...scope.querySelectorAll(selector)],
  $:(selector,scope)=>scope.querySelector(selector),
  requestAnimationFrame:cb=>cb(),
  getComputedStyle:()=>({lineHeight:'10px'}),
  livePlayerOperative:id=>({id,role:'Veteran',move:6,save:3,wounds:13}),
  playerDefinition:id=>({id,role:'Veteran',apl:3,move:6,save:3,wounds:13}),
  effectiveApl:()=>3,playerCurrentWounds:()=>13,
  experimentalDeathwatchGreenPortraitSvg:id=>'<svg>'+id+'</svg>',
  playerName:id=>id,escapeHtml:String,beginPlayerActivation:id=>{begun=id;}
});
bind(root);
check(elements['#confirmExperimentalRosterSelection'].disabled,
  'Begin Activation must remain disabled until an operative is chosen');
buttons[0].onclick();
check(elements['#confirmExperimentalRosterSelection'].disabled===false &&
  elements['#experimentalRosterDetailName'].textContent==='breacher',
  'Selecting the first operative failed to update detail or confirmation');
buttons[0].onkeydown({key:'ArrowRight',preventDefault(){}});
check(focused===buttons[1] && elements['#experimentalRosterDetailName'].textContent==='demolisher',
  'Keyboard selection failed');
elements['#confirmExperimentalRosterSelection'].onclick();
check(begun==='demolisher', 'Begin Activation did not start the selected operative');
""")


def test_release_gate_and_mobile_layout():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "experimentalFeaturesEnabled()&&teamName.toLowerCase()==='deathwatch'" in APP
    assert "if(inlineDeathwatchPicker)bindExperimentalDeathwatchRosterRail(inlineDeathwatchPicker);" in APP
    assert 'html[data-experimental="on"] .experimental-inline-deathwatch-card' in CSS
    assert "@media(max-width:600px)" in CSS
    assert "experimentalDeathwatchRosterMarkup(remainingPlayerOperatives(),{inline:true})" in APP
    assert "showExperimentalDeathwatchRosterRail(candidates);" in APP
