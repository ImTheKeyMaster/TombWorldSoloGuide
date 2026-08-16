import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
NARRATION = (ROOT / "narration.js").read_text()
STYLES = (ROOT / "styles.css").read_text()


class MasterNarrationResumeTests(unittest.TestCase):
    def run_node(self, body):
        result = subprocess.run(["node", "-e", body], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_release_schema_and_audio_architecture(self):
        self.assertEqual((8, 6, 95), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        ambient = (ROOT / "ambient.js").read_text()
        self.assertIn("new global.Audio()", ambient)
        self.assertNotIn("AudioContext", ambient)
        self.assertNotIn("webkitAudioContext", ambient)
        self.assertIn('"file": "Ambient/caverns.ogg"', (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        self.assertIn("await precacheAmbient(cache)", (ROOT / "service-worker.js").read_text())

    def test_master_pause_resume_preserves_production_media_and_activity(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');const players=[],events=[];let loads=0,removes=0;
class Audio{constructor(){this.paused=true;this.ended=false;this.currentTime=0;this.src='';players.push(this)}play(){this.paused=false;return Promise.resolve()}pause(){this.paused=true}load(){loads++}removeAttribute(){removes++;this.src=''}}
const s={Audio,URL,location:{href:'https://example.test/'},document:{},localStorage:{getItem:()=>null,setItem(){}},CustomEvent:function(type,options){this.type=type;this.detail=options?.detail},dispatchEvent(e){events.push(e)},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}})})};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('narration.js','utf8'),s);
(async()=>{const n=s.TombWorldNarration;await n.playMissionIntro('shifting-labyrinth');const production=players[0],src=production.src,loadsBefore=loads,removesBefore=removes;production.currentTime=7.4;n.setMasterEnabled(false);if(!production.paused||production.src!==src||production.currentTime!==7.4||loads!==loadsBefore||removes!==removesBefore)throw Error('mute destroyed production media');n.setMasterEnabled(true);if(!await n.activateFromGesture())throw Error('resume failed');if(players[0]!==production||production.src!==src||production.currentTime!==7.4||production.paused)throw Error('resume did not preserve media');const activity=events.filter(e=>e.type==='tombworldnarrationactivity').map(e=>e.detail.active);if(activity.join(',')!=='true,false,true')throw Error(`activity ${activity}`)})().catch(e=>{console.error(e);process.exit(1)});
""")

    def test_failed_resume_is_retryable_and_disabled_setting_discards_clip(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');const players=[];let reject=false,removes=0;
class Audio{constructor(){this.paused=true;this.ended=false;this.currentTime=3;this.src='';players.push(this)}play(){if(reject)return Promise.reject(Error('blocked'));this.paused=false;return Promise.resolve()}pause(){this.paused=true}load(){}removeAttribute(){removes++;this.src=''}}
const store={};const s={Audio,URL,location:{href:'https://example.test/'},document:{},localStorage:{getItem:k=>store[k]??null,setItem:(k,v)=>store[k]=v},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}})})};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('narration.js','utf8'),s);
(async()=>{const n=s.TombWorldNarration;await n.playMissionIntro('shifting-labyrinth');const p=players[0];n.setMasterEnabled(false);n.setMasterEnabled(true);reject=true;if(await n.activateFromGesture())throw Error('failed resume succeeded');if(!p.paused||p.currentTime!==3)throw Error('failed resume lost position');reject=false;if(!await n.activateFromGesture()||p.paused)throw Error('retry failed');n.setMasterEnabled(false);n.setPreferenceEnabled(false);n.setMasterEnabled(true);if(await n.activateFromGesture())throw Error('disabled narration resumed');if(!removes||p.src)throw Error('disabled narration was not discarded')})().catch(e=>{console.error(e);process.exit(1)});
""")

    def test_coordinator_and_platform_specific_menu(self):
        coordinator = APP[APP.index("function applySelectedAudioFromGesture") : APP.index("function handleNarrationUsable")]
        mission = APP[APP.index("$$('.mission-choice')") : APP.index("$('#setupHome')")]
        self.assertIn("TombWorldNarration.activateFromGesture()", coordinator)
        self.assertIn("TombWorldNarration.activateFromGesture()", mission)
        self.assertNotIn("TombWorldNarration.unlock({force:true})", APP)
        menu = APP[APP.index("function showGameMenu") : APP.index("function showAbout")]
        self.assertIn('supportsInAppVolumeControl()?`<div class="game-volume-row">', menu)
        self.assertIn('id="gameVolume" type="range"', menu)
        self.assertNotIn("Use device volume buttons", APP)
        self.assertNotIn("game-volume-device-message", APP + STYLES)
        self.assertIn('id="narrationToggle"', menu)
        self.assertIn('id="ambientNoiseToggle"', menu)

    def test_master_mute_is_non_destructive_but_explicit_stop_remains_destructive(self):
        master = NARRATION[NARRATION.index("function setMasterEnabled") : NARRATION.index("global.TombWorldNarration")]
        pause = NARRATION[NARRATION.index("function pauseForMasterMute") : NARRATION.index("function activateFromGesture")]
        stop = NARRATION[NARRATION.index("function stop(resetAudio") : NARRATION.index("function pauseNarration")]
        self.assertIn("pauseForMasterMute()", master)
        self.assertNotIn("stop(true)", master)
        self.assertNotIn("removeAttribute", pause)
        self.assertNotIn(".load(", pause)
        self.assertNotIn("playbackRequest", pause)
        self.assertNotIn("clearEventQueue", pause)
        self.assertNotIn("clearDeadlyEncounterQueue", pause)
        self.assertIn("clearEventQueue()", stop)
        self.assertIn("clearDeadlyEncounterQueue()", stop)
        self.assertIn("playbackRequest += 1", stop)


if __name__ == "__main__":
    unittest.main()
