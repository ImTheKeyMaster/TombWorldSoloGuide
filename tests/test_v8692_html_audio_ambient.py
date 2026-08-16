import json
import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


class HtmlAudioAmbientTests(unittest.TestCase):
    def test_release_source_and_web_audio_removal(self):
        self.assertEqual((8, 6, 92), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        for forbidden in ("AudioContext", "webkitAudioContext", "decodeAudioData", "createBufferSource", "createGain"):
            self.assertNotIn(forbidden, AMBIENT)
        self.assertEqual(1, AMBIENT.count("new global.Audio()"))
        config = json.loads((ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        self.assertEqual("Ambient/caverns.ogg", config["file"])
        self.assertIn("audio.loop = true", AMBIENT)
        self.assertIn("audio.preload = 'auto'", AMBIENT)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_gesture_calls_are_synchronous_and_menu_is_settings_only(self):
        gesture = AMBIENT[AMBIENT.index("function playFromGesture") : AMBIENT.index("function setActive")]
        self.assertIn("result = audio.play()", gesture)
        self.assertNotIn("await ", gesture[: gesture.index("audio.play()")])
        master = APP[APP.index("async function setGameAudioEnabled") : APP.index("function playPendingBoardSetupMissionIntro")]
        self.assertLess(master.index("TombWorldAmbient.playFromGesture()"), master.index("Promise.allSettled"))
        mission = APP[APP.index("$$('.mission-choice')") : APP.index("$('#setupHome')")]
        self.assertIn("TombWorldAmbient.playFromGesture()", mission)
        menu = APP[APP.index("function showGameMenu") : APP.index("function showAbout")]
        for operation in ("TombWorldAmbient.play", "TombWorldAmbient.stop", "TombWorldAmbient.reset", ".load()", "currentTime"):
            self.assertNotIn(operation, menu)
        self.assertIn("localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY,String(ambientEnabled))", menu)
        self.assertIn("TombWorldNarration.setPreferenceEnabled", menu)
        self.assertNotIn("setMasterEnabled", menu)

    def test_player_behavior_fades_ducks_recovers_and_resets(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let plays=0,loads=0,pauses=0,fail=false,now=1;const handlers={},timers=[];
class Audio{constructor(){Audio.instance=this;this.loop=false;this.preload='';this.src='';this.volume=1;this.paused=true;this.currentTime=12;this.listeners={}}addEventListener(t,h){this.listeners[t]=h}load(){loads++}play(){plays++;if(fail)return Promise.reject(Error('blocked'));this.paused=false;return Promise.resolve()}pause(){pauses++;this.paused=true}}
const document={visibilityState:'visible',addEventListener:(t,h)=>handlers[t]=h,removeEventListener:(t,h)=>{if(handlers[t]===h)delete handlers[t]}};
const config={schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.22,duckGain:.055,fadeInMs:1500,fadeOutMs:800,duckAttackMs:250,duckReleaseMs:700,loopStartSeconds:0,loopEndSeconds:null};
const s={Audio,URL,location:{href:'https://example.test/'},document,performance:{now:()=>now},requestAnimationFrame:h=>{now+=2000;h(now);return ++now},cancelAnimationFrame(){},setTimeout:h=>{timers.push(h);return timers.length},clearTimeout(){},fetch:async()=>({ok:true,json:async()=>config}),addEventListener:(t,h)=>handlers[t]=h,dispatchEvent(){},CustomEvent:class{constructor(t,o){this.type=t;this.detail=o.detail}}};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('ambient.js','utf8'),s);
(async()=>{const a=s.TombWorldAmbient,x=Audio.instance,near=(a,b)=>Math.abs(a-b)<1e-9;if(!await a.init()||loads!==1||plays)throw Error('init playback');a.setActive(true);if(!await a.playFromGesture()||plays!==1||!near(x.volume,.22))throw Error('initial play');handlers.tombworldnarrationactivity({detail:{active:true}});if(!near(x.volume,.055))throw Error('duck');handlers.tombworldnarrationactivity({detail:{active:false}});if(!near(x.volume,.22))throw Error('restore');a.stop();if(!near(x.volume,0)||pauses)throw Error('fade');a.setActive(true);await a.playFromGesture();timers.forEach(h=>h());if(x.paused||plays!==2)throw Error('stale pause');a.stop();timers.at(-1)();if(!x.paused)throw Error('pause');a.setActive(true);await a.playFromGesture();if(plays!==3)throw Error('resume');fail=true;await a.playFromGesture();await a.playFromGesture();if(typeof handlers.click!=='function')throw Error('recovery missing');const recovery=handlers.click;fail=false;recovery();await new Promise(resolve=>setImmediate(resolve));if(handlers.click||plays!==6)throw Error('recovery cleanup');a.reset();if(x.currentTime!==0||!x.paused)throw Error('reset');})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_offline_cache_and_narration_isolation(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("`./Assets/Audio/Narration/${file}`", worker)
        self.assertIn("await precacheAmbient(cache)", worker)
        self.assertNotIn("TombWorldAmbient", (ROOT / "narration.js").read_text(encoding="utf-8"))
        self.assertNotIn("playMissionIntro", AMBIENT)


if __name__ == "__main__":
    unittest.main()
