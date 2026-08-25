import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


class AudioSettingsMasterTests(unittest.TestCase):
    def test_release_metadata_and_save_version(self):
        self.assertEqual((8, 6, 91), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "narration.js", "ambient.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", index)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", worker)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text(encoding="utf-8"))

    def test_preferences_master_and_applied_state_are_separate(self):
        self.assertIn("const MASTER_ENABLED_KEY = 'tombWorldBattleGuide.gameAudioEnabled';", NARRATION)
        self.assertIn("setPreferenceEnabled, isPreferenceEnabled, setMasterEnabled, isMasterEnabled, isPlaybackEnabled", NARRATION)
        self.assertIn("let appliedAmbientEnabled=TombWorldNarration.isMasterEnabled()&&ambientEnabled", APP)
        self.assertIn("return TombWorldNarration.isMasterEnabled()&&appliedAmbientEnabled", APP)
        self.assertNotIn("TombWorldNarration.isEnabled()", APP + AMBIENT)
        self.assertNotIn("TombWorldNarration.setEnabled(", APP)

    def test_menu_toggles_only_write_preferences(self):
        menu = APP[APP.index("function showGameMenu()") : APP.index("function showAbout()")]
        self.assertIn('id="narrationToggle"', menu)
        self.assertNotIn('id="gameAudioToggle"', menu)
        narration_handler = menu[menu.index("$('#narrationToggle').onclick") : menu.index("$('#ambientNoiseToggle').onclick")]
        ambient_handler = menu[menu.index("$('#ambientNoiseToggle').onclick") : menu.index("$('#menuAbout').onclick")]
        self.assertIn("setPreferenceEnabled", narration_handler)
        self.assertNotRegex(narration_handler, r"unlock|stop|setActive|reconcile|setMaster")
        self.assertIn("localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY", ambient_handler)
        self.assertNotRegex(ambient_handler, r"unlock|stop|setActive|reconcile|setMaster")

    def test_master_does_not_modify_preferences(self):
        master = APP[APP.index("async function setGameAudioEnabled") : APP.index("function playPendingBoardSetupMissionIntro")]
        self.assertIn("TombWorldNarration.setMasterEnabled(enabled)", master)
        self.assertIn("appliedAmbientEnabled=ambientEnabled", master)
        self.assertIn("appliedAmbientEnabled=false", master)
        self.assertNotIn("setPreferenceEnabled", master)
        self.assertNotIn("AMBIENT_ENABLED_PREFERENCE_KEY", master)
        self.assertIn("Master audio ${masterEnabled?'on':'off'}", APP)

    def test_narration_preference_is_silent_until_master_reactivation(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const store=new Map(),events=[];let pauses=0,plays=0;
class CustomEvent{constructor(type,options={}){this.type=type;this.detail=options.detail;}}
class Audio{constructor(){Audio.instance=this;this.paused=true;this.ended=false;this.src='';}play(){plays++;this.paused=false;return Promise.resolve();}pause(){pauses++;this.paused=true;}removeAttribute(name){if(name==='src')this.src='';}load(){}}
const document={addEventListener(){},removeEventListener(){}};
const context={Audio,CustomEvent,document,URL,location:{href:'https://example.test/'},localStorage:{getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>store.set(k,v)},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}})}),dispatchEvent:e=>events.push(e)};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;await n.init();
if(!n.isPreferenceEnabled()||!n.isMasterEnabled()||!n.isPlaybackEnabled())throw Error('missing values did not default on');
await n.playMissionIntro('shifting-labyrinth');const playingPauses=pauses;
n.setPreferenceEnabled(false);
if(store.get('tombWorldBattleGuide.narrationEnabled')!=='false'||pauses!==playingPauses||!n.isPlaybackEnabled())throw Error('preference off altered live playback');
n.setPreferenceEnabled(true);
if(plays!==1||!n.isPlaybackEnabled())throw Error('preference on started playback');
n.setMasterEnabled(false);
if(store.get('tombWorldBattleGuide.gameAudioEnabled')!=='false'||store.get('tombWorldBattleGuide.narrationEnabled')!=='true'||n.isPlaybackEnabled()||pauses===playingPauses)throw Error('master off was not independent/destructive');
n.setPreferenceEnabled(false);n.setMasterEnabled(true);
if(!n.isMasterEnabled()||n.isPlaybackEnabled()||store.get('tombWorldBattleGuide.narrationEnabled')!=='false')throw Error('master on did not apply latest preference');
n.setPreferenceEnabled(true);
if(n.isPlaybackEnabled())throw Error('stored preference leaked into applied state');
n.setMasterEnabled(false);n.setMasterEnabled(true);
if(!n.isPlaybackEnabled())throw Error('master cycle did not apply latest narration preference');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_explicit_narration_unlock_uses_dedicated_player_without_global_fallback(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const listeners=new Map(),players=[];let plays=0,removals=0;
class Audio{constructor(){this.src='';players.push(this);}play(){plays++;return Promise.resolve();}pause(){}removeAttribute(){}load(){}}
const document={
 addEventListener:(type,handler)=>listeners.set(type,handler),
 removeEventListener:(type,handler)=>{if(listeners.get(type)===handler){listeners.delete(type);removals++;}}
};
const context={Audio,URL,document,location:{href:'https://example.test/'},localStorage:{getItem:()=>null,setItem(){}},fetch:async()=>({ok:false})};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;
if(listeners.has('click'))throw Error('narration installed a global click fallback');
await n.init();
await n.unlock();
if(plays!==1||players.length!==2||players[0].src)throw Error('silent prime did not use a separate unlock-only player');
await n.unlock();
if(plays!==1||removals!==0||listeners.has('click'))throw Error('unlocked narration retried or installed gesture work');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_master_off_cancels_inflight_narration_without_reporting_playback(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let resolvePlay;
class CustomEvent{constructor(type,options={}){this.type=type;this.detail=options.detail;}}
class Audio{constructor(){this.paused=false;this.ended=false;this.src='';}play(){return new Promise(resolve=>resolvePlay=resolve);}pause(){this.paused=true;}removeAttribute(){this.src='';}load(){}}
const context={Audio,CustomEvent,URL,document:{addEventListener(){},removeEventListener(){}},location:{href:'https://example.test/'},localStorage:{getItem:()=>null,setItem(){}},dispatchEvent(){},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}})})};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;await n.init();
const pending=n.playMissionIntro('shifting-labyrinth');while(!resolvePlay)await Promise.resolve();
n.setMasterEnabled(false);resolvePlay();
if(await pending)throw Error('cancelled narration reported successful playback');
if(n.canReplay())throw Error('cancelled narration became replayable');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_ambient_asset_unlock_and_ducking_contract_remains(self):
        config = (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn('"file": "Ambient/caverns.ogg"', config)
        self.assertIn("await cache.add(`./Assets/Audio/Narration/${file}`)", worker)
        self.assertIn("tombworldnarrationactivity", AMBIENT)
        self.assertIn("duckGain", AMBIENT)
        self.assertNotIn("tombworldnarrationchange", AMBIENT)
        self.assertNotIn("global.document.addEventListener('click'", AMBIENT)


if __name__ == "__main__":
    unittest.main()
