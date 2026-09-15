import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = (ROOT / "narration-transcript.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def run_node(source):
    result = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_release_surfaces_and_save_contract():
    assert CURRENT_APP_VERSION == "10.0.13"
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT / "service-worker.js").read_text()
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 11
    assert f"analytics.js?release={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text()
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in (ROOT / "app.js").read_text()


def test_play_resume_and_pause_use_only_silent_enabled_dice_activation():
    handler = TRANSCRIPT.split("pause.addEventListener('click'", 1)[1].split("skip.addEventListener", 1)[0]
    helper = TRANSCRIPT.split("function activateDiceFromNarrationGesture", 1)[1].split("hide.addEventListener", 1)[0]
    assert "dice?.isPreferenceEnabled?.()" in helper
    assert "dice.activateFromGesture()" in helper
    assert "Promise.resolve" in helper and ".catch(() => false)" in helper
    assert "activateDiceFromNarrationGesture();\n        await narration.startNarration();" in handler
    assert "activateDiceFromNarrationGesture();\n        await narration.resumeNarration();" in handler
    assert handler.count("activateDiceFromNarrationGesture()") == 2
    assert "TombWorldDiceSfx.play" not in TRANSCRIPT
    assert "TombWorldAmbient" not in TRANSCRIPT
    pause_branch = handler.split("else narration.pauseNarration()", 1)[0].rsplit("}", 1)[1]
    assert "activateDiceFromNarrationGesture" not in pause_branch


def test_ambient_off_narration_play_and_resume_recover_suspended_dice_end_to_end():
    run_node(r"""
const fs=require('fs'),vm=require('vm');
const stored=new Map([['tombWorldBattleGuide.ambientEnabled','false'],['tombWorldBattleGuide.diceRollEnabled','true']]);
let starts=0,resumes=0,startNarrationCalls=0,resumeNarrationCalls=0,ambientStarts=0;
class Context{
 constructor(){this.state='suspended';this.destination={};Context.instance=this}
 createGain(){return {gain:{value:1},connect(){}}}
 createBufferSource(){return {connect(){},start(){starts++},stop(){}}}
 decodeAudioData(){return Promise.resolve({decoded:true})}
 resume(){resumes++;this.state='running';return Promise.resolve()}
}
const elements={},fill={style:{}};
function element(id){return elements[id]={id,hidden:false,open:false,isConnected:true,style:{},attributes:{},children:[],listeners:{},classList:{add(){},remove(){}},addEventListener(type,fn){this.listeners[type]=fn},setAttribute(name,value){this.attributes[name]=value},removeAttribute(name){delete this.attributes[name]},replaceChildren(...children){this.children=children},focus(){document.activeElement=this},close(){this.open=false},showModal(){this.open=true},querySelector(){return fill},scrollTo(){}}}
for(const id of ['narrationTranscriptDialog','narrationTranscriptReopen','narrationTranscriptCategory','narrationTranscriptBody','narrationTranscriptProgress','narrationTranscriptTime','narrationTranscriptHide','narrationTranscriptPause','narrationTranscriptSkip','narrationTranscriptStop','narrationTranscriptPauseHelp'])element(id);
const rootClasses=new Set();
const document={readyState:'complete',activeElement:null,documentElement:{scrollTop:0,classList:{contains:v=>rootClasses.has(v),add:v=>rootClasses.add(v),remove:v=>rootClasses.delete(v)}},body:{style:{}},getElementById:id=>elements[id],createElement:tag=>({tag,textContent:'',classList:{add(){}},dataset:{}}),createTextNode:text=>({text})};
let state={active:true,id:'event.test',category:'event',started:false,playing:false,paused:false,pausedByUser:false,pausedByMaster:false,currentTimeMs:0,durationMs:1000,transcriptAvailable:false};
const narration={getPlaybackState:()=>state,isMasterEnabled:()=>true,async startNarration(){startNarrationCalls++;state={...state,started:true,playing:true};return true},pauseNarration(){state={...state,playing:false,paused:true,pausedByUser:true};return true},async resumeNarration(){resumeNarrationCalls++;state={...state,playing:true,paused:false,pausedByUser:false};return true},skipCurrent(){},stop(){}};
const localStorage={getItem:key=>stored.get(key)??null,setItem:(key,value)=>stored.set(key,value)};
const context={AudioContext:Context,document,localStorage,fetch:async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(1)}),TombWorldNarration:narration,TombWorldAmbient:{playFromGesture(){ambientStarts++}},Promise,Set,scrollY:0,scrollTo(){},requestAnimationFrame:()=>1,cancelAnimationFrame(){},addEventListener(){}};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync('dice-sfx.js','utf8'),context);vm.runInContext(fs.readFileSync('narration-transcript.js','utf8'),context);
const dice=context.TombWorldDiceSfx,button=elements.narrationTranscriptPause,flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
 await button.listeners.click();await flush();
 if(Context.instance.state!=='running'||resumes!==1||starts!==0||startNarrationCalls!==1)throw Error('Play did not silently resume Dice alongside narration');
 if(!await dice.play()||starts!==1)throw Error('automatic roll after Play was not audible exactly once');
 Context.instance.state='suspended';state={...state,playing:false,paused:true,pausedByUser:true};
 await button.listeners.click();await flush();
 if(Context.instance.state!=='running'||resumes!==2||starts!==1||resumeNarrationCalls!==1)throw Error('Resume did not silently recover suspended Dice');
 if(!await dice.play()||starts!==2)throw Error('automatic roll after Resume was not audible exactly once');
 if(stored.get('tombWorldBattleGuide.ambientEnabled')!=='false'||stored.get('tombWorldBattleGuide.diceRollEnabled')!=='true'||ambientStarts)throw Error('audio preferences or Ambient changed');
})().catch(error=>{console.error(error);process.exit(1)});
""")


def test_dice_off_master_off_pause_and_activation_failures_preserve_narration():
    run_node(r"""
const fs=require('fs'),vm=require('vm');
const elements={},fill={style:{}};function element(id){return elements[id]={hidden:false,open:false,isConnected:true,style:{},listeners:{},classList:{add(){},remove(){}},addEventListener(t,f){this.listeners[t]=f},setAttribute(){},removeAttribute(){},replaceChildren(){},focus(){},showModal(){this.open=true},close(){this.open=false},querySelector(){return fill},scrollTo(){}}}
for(const id of ['narrationTranscriptDialog','narrationTranscriptReopen','narrationTranscriptCategory','narrationTranscriptBody','narrationTranscriptProgress','narrationTranscriptTime','narrationTranscriptHide','narrationTranscriptPause','narrationTranscriptSkip','narrationTranscriptStop','narrationTranscriptPauseHelp'])element(id);
const document={readyState:'complete',activeElement:null,documentElement:{scrollTop:0,classList:{contains:()=>false,add(){},remove(){}}},body:{style:{}},getElementById:id=>elements[id],createElement:()=>({textContent:''})};
let state={active:true,id:'test',started:false,playing:false,pausedByUser:false,pausedByMaster:false,currentTimeMs:0,durationMs:1},master=true,enabled=true,throwActivation=false,activations=0,starts=0,resumes=0,pauses=0;
const narration={getPlaybackState:()=>state,isMasterEnabled:()=>master,async startNarration(){starts++;state={...state,started:true,playing:true};return true},async resumeNarration(){resumes++;state={...state,pausedByUser:false};return true},pauseNarration(){pauses++},skipCurrent(){},stop(){}};
const dice={isPreferenceEnabled:()=>enabled,activateFromGesture(){activations++;if(throwActivation)throw Error('blocked synchronously');return Promise.reject(Error('blocked'))}};
const context={document,TombWorldNarration:narration,TombWorldDiceSfx:dice,Promise,scrollY:0,scrollTo(){},requestAnimationFrame:()=>1,cancelAnimationFrame(){},addEventListener(){}};context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration-transcript.js','utf8'),context);const click=elements.narrationTranscriptPause.listeners.click;
(async()=>{
 await click();if(starts!==1||activations!==1)throw Error('rejected Dice activation blocked Narration Play');
 state={...state,playing:false,pausedByUser:true};throwActivation=true;await click();if(resumes!==1||activations!==2)throw Error('thrown Dice activation blocked Resume');
 state={...state,playing:true,pausedByUser:false};await click();if(pauses!==1||activations!==2)throw Error('Pause activated Dice');
 state={...state,started:false};enabled=false;throwActivation=false;await click();if(starts!==2||activations!==2)throw Error('Dice Off activation or Narration Play failed');
 state={...state,started:false};master=false;enabled=true;await click();if(starts!==2||activations!==2)throw Error('Master Off was not authoritative');
})().catch(error=>{console.error(error);process.exit(1)});
""")
