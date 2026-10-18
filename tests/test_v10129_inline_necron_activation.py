"""Experimental-only inline Necron activation: parity with the Deathwatch preview."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def run_js(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_inline_and_standard_necron_activation_card_modes():
    run_js(r"""
const fs=require('node:fs'),app=fs.readFileSync('app.js','utf8');
const block=(a,b)=>app.slice(app.indexOf(a),app.indexOf(b,app.indexOf(a)));
const body=block('function nextStepCard(){','function missionStrategyPending()');
const create=new Function('d','const {state,setNextActivation,playerOperativesRemaining,'+
  'activationSideName,experimentalFeaturesEnabled,activePlayerActivation,playerName,'+
  'experimentalDeathwatchRosterMarkup,remainingPlayerOperatives,activationProgressLabel,'+
  'escapeHtml,skipRemainingActivationsControl,activationModelLabel,readyNpos,isPvpMode,'+
  'opponentSingularLabel,experimentalNecronRosterMarkup}=d;'+body+';return nextStepCard');
const check=(condition,why)=>{if(!condition)throw Error(why);};
function card({experimental=false,side='npo',active=false,count=2}={}){
  const state={completed:false,phase:'firefight',nextSide:side,npoActivated:1,
    playerActivated:1,activeNpoId:active?'n1':null,
    lastActivation:active?{npoId:'n1',name:'Necron Warrior',committed:false}:null};
  return create({state,setNextActivation:()=>{},playerOperativesRemaining:()=>4,
    activationSideName:()=> 'Deathwatch',experimentalFeaturesEnabled:()=>experimental,
    activePlayerActivation:()=>null,playerName:String,
    experimentalDeathwatchRosterMarkup:()=>'<div>DEATHWATCH</div>',
    remainingPlayerOperatives:()=>['p1'],activationProgressLabel:()=> '2 OF 13',
    escapeHtml:String,skipRemainingActivationsControl:()=>'<button id="skipRemainingActivations"></button>',
    activationModelLabel:()=> 'Necron',
    readyNpos:()=>Array.from({length:count},(_,i)=>({id:'n'+i})),
    isPvpMode:()=>false,opponentSingularLabel:()=> 'Necron',
    experimentalNecronRosterMarkup:(list,options)=>
      '<section id="experimentalInlineNecronPicker">'+list.length+':'+options.inline+'</section>'
  })();
}
const standard=card(),inline=card({experimental:true});
check(standard.includes('id="npoActivation"')&&!standard.includes('experimentalInlineNecronPicker'),
  'Standard mode must keep the Activate a Necron button');
check(inline.includes('id="experimentalInlineNecronPicker"')&&
  inline.includes('id="skipRemainingActivations"')&&!inline.includes('id="npoActivation"'),
  'Experimental mode must replace the button with the roster and Skip Remaining');
check(card({experimental:true,count:1}).includes('1:true'),
  'Experimental mode should show the single ready Necron');
check(card({experimental:true,active:true}).includes('Resume Activation')&&
  !card({experimental:true,active:true}).includes('experimentalInlineNecronPicker'),
  'An unfinished activation must resume instead of showing another selector');
check(card({experimental:true,side:'player'}).includes('DEATHWATCH'),
  'Deathwatch preview must remain unaffected');
""")


def test_reusable_necron_rail_supports_inline_modal_keyboard_and_stale_selection():
    run_js(r"""
const fs=require('node:fs'),app=fs.readFileSync('app.js','utf8');
const block=(a,b)=>app.slice(app.indexOf(a),app.indexOf(b,app.indexOf(a)));
const check=(condition,why)=>{if(!condition)throw Error(why);};
const markup=block('function experimentalNecronRosterMarkup(',
  'function showExperimentalNecronRosterRail(');
const createMarkup=new Function('sortedNposForDisplay','experimentalNecronPortraitMarkup',
  'npoName','escapeHtml','isPvpMode','playerSideLabel',
  markup+';return experimentalNecronRosterMarkup');
const mk=createMarkup(list=>list,n=>'<svg>'+n.id+'</svg>',n=>n.name,
  String,()=>false,()=> 'Deathwatch');
const npos=[{id:'n1',name:'Warrior 1'},{id:'n2',name:'Scarab'}];
const inline=mk(npos,{inline:true}),modal=mk(npos);
check(inline.includes('id="experimentalInlineNecronPicker"')&&
  !inline.includes('data-close>Close Guide'),'Inline picker should not have Close Guide');
check(modal.includes('data-close>Close Guide')&&
  !modal.includes('experimentalInlineNecronPicker'),'Standard modal markup changed');
check(inline.includes('Threat Principle')&&inline.includes('role="radiogroup"'),
  'Threat Principle instruction or roster semantics missing');
check(mk([...npos,...npos,...npos]).includes('is-overflowing'),
  'Large Necron rosters should preserve horizontal scrolling');

let ready=[...npos],begun=[],renders=0,toasts=0,closed=0,resumed=0,focused=null;
const classes=()=>({add(){},remove(){},toggle(){}});
const buttons=npos.map(n=>({dataset:{rosterNpo:n.id},classList:classes(),
  querySelector:()=>({scrollHeight:10}),setAttribute(k,v){this[k]=v;},
  focus(){focused=this;}}));
const ids=['#confirmExperimentalNecronSelection','#experimentalNecronRosterDetailImage',
  '#experimentalNecronRosterDetailName','#experimentalNecronRosterDetailRole',
  '#experimentalNecronRosterStats'];
const nodes=Object.fromEntries(ids.map(id=>[id,{disabled:true,
  classList:classes(),innerHTML:'',textContent:'',removeAttribute(){}}]));
const root={id:'experimentalInlineNecronPicker',
  querySelector:id=>nodes[id],
  querySelectorAll:id=>id==='[data-roster-npo]'?buttons:[]};
const state={activeNpoId:null,lastActivation:null};
const binding=block('function bindExperimentalNecronRosterRail(',
  'function experimentalDeathwatchRosterMarkup(');
const bind=new Function('d','const {$$,$,requestAnimationFrame,getComputedStyle,'+
  'readyNpos,npoDefinition,npoWeapon,effectiveApl,experimentalNecronPortraitMarkup,'+
  'npoName,escapeHtml,beginNpoActivation,closeModal,render,showToast,state,'+
  'continueNpoActivation}=d;'+binding+';return bindExperimentalNecronRosterRail')({
    $$:(selector,scope)=>[...scope.querySelectorAll(selector)],
    $:(selector,scope)=>scope.querySelector(selector),
    requestAnimationFrame:cb=>cb(),getComputedStyle:()=>({lineHeight:'10px'}),
    readyNpos:()=>ready,
    npoDefinition:()=>({apl:2,move:6,save:3,wounds:7,faction:'Necron'}),
    npoWeapon:()=>({name:'Gauss'}),effectiveApl:()=>2,
    experimentalNecronPortraitMarkup:n=>'<svg>'+n.id+'</svg>',
    npoName:n=>n.name,escapeHtml:String,
    beginNpoActivation:(n,options)=>begun.push([n,options]),
    closeModal:()=>closed++,render:()=>renders++,showToast:()=>toasts++,
    state,continueNpoActivation:()=>resumed++
  });
bind(root);
check(nodes[ids[0]].disabled,'Begin Activation must start disabled');
buttons[0].onclick();
check(!nodes[ids[0]].disabled&&nodes[ids[2]].textContent==='Warrior 1',
  'Selecting a Necron must populate its detail panel');
buttons[0].onkeydown({key:'ArrowRight',preventDefault(){}});
check(focused===buttons[1]&&nodes[ids[2]].textContent==='Scarab',
  'Keyboard arrow must select the next Necron');
nodes[ids[0]].onclick();
check(begun.length===1&&begun[0][0].id==='n2'&&
  begun[0][1].refreshPlayCard===true,'Inline Begin must refresh the card');
ready=[];nodes[ids[0]].onclick();
check(begun.length===1&&renders===1&&toasts===1&&closed===0,
  'A stale inline selection should refresh and warn, not open another activation');
state.activeNpoId='n1';state.lastActivation={npoId:'n1',committed:false};
nodes[ids[0]].onclick();
check(resumed===1&&begun.length===1,'A second click must resume the active Necron');
state.activeNpoId=null;state.lastActivation=null;ready=[...npos];
const modalRoot={...root,id:'standardNecronDialog'};
bind(modalRoot);
buttons[0].onclick();nodes[ids[0]].onclick();
check(begun.length===2&&begun[1][0].id==='n1'&&
  begun[1][1].refreshPlayCard===false,
  'Standard modal Begin Activation should preserve its existing non-refresh flow');
ready=[];nodes[ids[0]].onclick();
check(closed===1&&toasts===2,
  'A stale selection in Standard mode should close its dialog and show a warning');
""")


def test_necron_begin_refreshes_card_before_wizard_and_keeps_standard_unchanged():
    begin = APP.split("function beginNpoActivation(", 1)[1].split("function showNpoSelection()", 1)[0]
    assert "refreshPlayCard=false" in begin
    assert begin.index("save();") < begin.index("if(refreshPlayCard)render();") < begin.index("continueNpoActivation();")
    assert "beginNpoActivation(n,{refreshPlayCard:root.id==='experimentalInlineNecronPicker'})" in APP
    assert "showExperimentalNecronRosterRail(candidates);" in APP
    assert "if(inlineNecronPicker)bindExperimentalNecronRosterRail(inlineNecronPicker);" in APP


def test_necron_release_and_styles_are_opt_in_only():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "Experimental Features" in INDEX and "Deathwatch and Necron activation cards" in INDEX
    assert 'html[data-experimental="on"] .experimental-inline-necron-card' in CSS
    assert "html[data-experimental=\"on\"] .experimental-inline-deathwatch-card" in CSS
    assert "@media(max-width:600px)" in CSS
