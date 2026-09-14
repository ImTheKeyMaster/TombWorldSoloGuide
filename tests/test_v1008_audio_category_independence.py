import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
DICE = (ROOT / "dice-sfx.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


def handler(start, end):
    menu = APP[APP.index("function showGameMenu()") : APP.index("function showAbout()")]
    return menu[menu.index(start) : menu.index(end)]


def run_node(script):
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_v1008_release_and_save_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (10, 0, 9)
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_category_toggle_ownership_and_immediate_actions():
    narration = handler("$('#narrationToggle').onclick", "$('#ambientNoiseToggle').onclick")
    ambient = handler("$('#ambientNoiseToggle').onclick", "$('#diceRollToggle').onclick")
    dice = handler("$('#diceRollToggle').onclick", "const gameVolume=")

    assert "localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY,String(ambientEnabled))" in ambient
    assert "TombWorldAmbient.playFromGesture()" in ambient
    assert "TombWorldAmbient.stop()" in ambient
    assert "TombWorldDiceSfx" not in ambient

    assert "TombWorldDiceSfx.setPreferenceEnabled(enabled)" in dice
    assert "TombWorldDiceSfx.activateFromGesture()" in dice
    assert "TombWorldDiceSfx.stop()" in dice
    assert "TombWorldDiceSfx.play()" not in dice
    assert "TombWorldAmbient" not in dice
    assert "ambientEnabled" not in dice
    assert "TombWorldNarration.set" not in dice

    assert "ambientEnabled" not in narration
    assert "TombWorldDiceSfx" not in narration


def test_dice_runtime_is_web_audio_and_has_independent_recovery():
    assert "window.AudioContext || window.webkitAudioContext" in DICE
    assert "decodeAudioData(data)" in DICE
    assert "decodedDiceBuffer" in DICE
    assert "tombworldaudiorecoveryrequired" in DICE
    assert "category: 'dice'" in DICE
    assert "TombWorldAmbient" not in DICE
    assert "TombWorldNarration" not in DICE
    assert "desiredActive" not in DICE
    activation = DICE[DICE.index("function activateFromGesture") : DICE.index("function setPreferenceEnabled")]
    assert "context.resume()" in activation
    assert "startSource" not in activation


def test_master_preserves_preferences_and_ambient_ducking():
    master = APP[APP.index("async function setGameAudioEnabled") : APP.index("function playPendingBoardSetupMissionIntro")]
    assert "TombWorldNarration.setMasterEnabled(enabled)" in master
    assert "TombWorldDiceSfx.setMasterEnabled(enabled)" in master
    assert "TombWorldDiceSfx.setPreferenceEnabled" not in master
    assert "localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY" not in master
    assert "appliedAmbientEnabled=ambientEnabled" in master
    assert "tombworldnarrationactivity" in AMBIENT
    assert "duckGain" in AMBIENT


def test_runtime_matrix_and_reload_preferences_are_independent():
    script = r"""
const fs=require('fs'),vm=require('vm');
const stored=new Map([
 ['tombWorldBattleGuide.ambientEnabled','true'],
 ['tombWorldBattleGuide.diceRollEnabled','true']
]);
let starts=0,ambientStarts=0,ambientStops=0;
class Context{
 constructor(){this.state='running';this.destination={}}
 createGain(){return {gain:{value:1},connect(){}}}
 createBufferSource(){return {connect(){},start(){starts++},stop(){}}}
 decodeAudioData(){return Promise.resolve({buffer:true})}
 resume(){this.state='running';return Promise.resolve()}
}
const localStorage={getItem:k=>stored.get(k)??null,setItem:(k,v)=>stored.set(k,v)};
const window={AudioContext:Context,localStorage,fetch:async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(1)})};
window.window=window;
const sandbox={window,localStorage,fetch:window.fetch,Promise,Set};
vm.runInNewContext(fs.readFileSync('dice-sfx.js','utf8'),sandbox);
const dice=window.TombWorldDiceSfx;
let ambientEnabled=localStorage.getItem('tombWorldBattleGuide.ambientEnabled')!=='false';
const setAmbient=enabled=>{ambientEnabled=enabled;localStorage.setItem('tombWorldBattleGuide.ambientEnabled',String(enabled));enabled?ambientStarts++:ambientStops++};
(async()=>{
 await dice.init();
 if(!await dice.play()||starts!==1)throw Error('initial dice play failed');
 setAmbient(false);
 if(ambientStops!==1||!dice.isPreferenceEnabled()||!await dice.play()||starts!==2)throw Error('ambient off coupled dice');
 dice.setPreferenceEnabled(false);dice.stop();
 if(await dice.play()||ambientEnabled)throw Error('dice off changed ambient or played');
 setAmbient(true);
 if(await dice.play()||!ambientEnabled||ambientStarts!==1)throw Error('ambient on changed dice');
 if(stored.get('tombWorldBattleGuide.ambientEnabled')!=='true'||stored.get('tombWorldBattleGuide.diceRollEnabled')!=='false')throw Error('preferences coupled');
 const reloadedAmbient=localStorage.getItem('tombWorldBattleGuide.ambientEnabled')!=='false';
 if(!reloadedAmbient||localStorage.getItem('tombWorldBattleGuide.diceRollEnabled')!=='false')throw Error('reload changed preferences');
})().catch(error=>{console.error(error);process.exit(1)});
"""
    run_node(script)


def test_suspended_context_failure_then_later_gesture_recovers_silently():
    script = r"""
const fs=require('fs'),vm=require('vm');let blocked=true,resumes=0,starts=0;const events=[];
class CustomEvent{constructor(type,options){this.type=type;this.detail=options.detail}}
class Context{
 constructor(){this.state='suspended';this.destination={}}
 createGain(){return {gain:{value:1},connect(){}}}
 createBufferSource(){return {connect(){},start(){starts++},stop(){}}}
 decodeAudioData(){return Promise.resolve({buffer:true})}
 resume(){resumes++;if(blocked)return Promise.reject(Error('gesture required'));this.state='running';return Promise.resolve()}
}
const window={AudioContext:Context,CustomEvent,dispatchEvent:event=>events.push(event),localStorage:{getItem:()=>null,setItem(){}},fetch:async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(1)})};window.window=window;
const sandbox={window,localStorage:window.localStorage,fetch:window.fetch,CustomEvent,Promise,Set};
vm.runInNewContext(fs.readFileSync('dice-sfx.js','utf8'),sandbox);const dice=window.TombWorldDiceSfx;
(async()=>{
 await dice.init();
 if(await dice.play()||events.at(-1)?.detail?.category!=='dice')throw Error('failed resume did not request dice recovery');
 blocked=false;
 if(!await dice.activateFromGesture()||starts!==0||resumes!==2)throw Error('gesture recovery was not silent and independent');
 if(!await dice.play()||starts!==1)throw Error('playback did not recover');
})().catch(error=>{console.error(error);process.exit(1)});
"""
    run_node(script)
