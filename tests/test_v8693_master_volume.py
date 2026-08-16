import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


class MasterVolumeTests(unittest.TestCase):
    def test_release_storage_and_save_contract(self):
        self.assertEqual(".".join(map(str, (8, 6, 94))), CURRENT_APP_VERSION)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        self.assertIn("tombWorldSoloGuide.gameVolume", APP)
        self.assertIn("return Number.isFinite(saved)&&saved>=0.01&&saved<=1?saved:1", APP)
        self.assertIn("catch{return 1;}", APP)
        self.assertNotIn("GAME_VOLUME_PREFERENCE_KEY", (ROOT / "persistence.js").read_text())
        new_game = APP[APP.index("function startNewGameSetup") : APP.index("function confirmNewGame")]
        self.assertNotIn("GAME_VOLUME_PREFERENCE_KEY", new_game)

    def test_native_accessible_range_and_endpoint_glyphs(self):
        menu = APP[APP.index("function showGameMenu") : APP.index("function showAbout")]
        self.assertIn('<label for="gameVolume">Volume</label>', menu)
        self.assertIn('id="gameVolume" type="range" min="0" max="100" step="1"', menu)
        self.assertEqual(2, menu.count('class="game-volume-icon"'))
        self.assertEqual(2, menu.count('aria-hidden="true" focusable="false"'))
        self.assertLess(menu.index("M16 9 L21 15"), menu.index('id="gameVolume"'))
        self.assertGreater(menu.index("M19 6c2.7"), menu.index('id="gameVolume"'))
        self.assertIn("aria-valuetext", menu)
        self.assertIn(".oninput=event=>", menu)

    def test_master_slider_state_and_category_independence(self):
        sync = APP[APP.index("function syncNarrationControls") : APP.index("async function setGameAudioEnabled")]
        self.assertIn("masterEnabled?Math.round(preferredGameVolume*100):0", sync)
        self.assertIn("percentage===0?'Muted':`${percentage} percent`", sync)
        handler = APP[APP.index("const gameVolume=$('#gameVolume')") : APP.index("$('#menuAbout').onclick")]
        self.assertIn("if(percentage===0)", handler)
        self.assertIn("setGameAudioEnabled(false)", handler)
        self.assertIn("writePreferredGameVolume()", handler)
        self.assertLess(handler.index("TombWorldAmbient.setVolumeMultiplier"), handler.index("writePreferredGameVolume()"))
        self.assertIn("if(!TombWorldNarration.isMasterEnabled())void setGameAudioEnabled(true)", handler)
        self.assertNotIn("setPreferenceEnabled", handler)
        self.assertNotIn("AMBIENT_ENABLED_PREFERENCE_KEY", handler)
        master = APP[APP.index("async function setGameAudioEnabled") : APP.index("function playPendingBoardSetupMissionIntro")]
        self.assertNotIn("GAME_VOLUME_PREFERENCE_KEY", master)
        self.assertLess(master.index("TombWorldAmbient.playFromGesture()"), master.index("Promise.allSettled"))

    def test_narration_multiplier_is_live_future_safe_and_unlock_is_full_volume(self):
        script = r"""
const fs=require('fs'),vm=require('vm');const players=[];
class Audio{constructor(){this.volume=.4;this.paused=true;this.ended=false;this.src='';players.push(this)}play(){this.paused=false;return Promise.resolve()}pause(){this.paused=true}removeAttribute(){this.src=''}load(){}}
const s={Audio,URL,location:{href:'https://example.test/'},document:{},localStorage:{getItem:()=>null,setItem(){}},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}})})};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('narration.js','utf8'),s);
(async()=>{const n=s.TombWorldNarration;n.setVolumeMultiplier(.65);await n.init();if(players[0].volume!==.65)throw Error('future player');await n.unlock();if(players[1].volume!==1)throw Error('unlock volume');await n.playMissionIntro('shifting-labyrinth');if(players[0].volume!==.65)throw Error('play reset');n.setVolumeMultiplier(.25);if(players[0].volume!==.25||players[1].volume!==1)throw Error('live volume');n.setVolumeMultiplier(5);if(players[0].volume!==1)throw Error('upper clamp');n.setVolumeMultiplier(-2);if(players[0].volume!==0)throw Error('lower clamp')})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_ambient_multiplier_scales_live_ducking_without_media_restart(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let plays=0,loads=0;const handlers={};
class Audio{constructor(){Audio.instance=this;this.volume=0;this.paused=true;this.currentTime=17;this.listeners={}}addEventListener(t,h){this.listeners[t]=h}load(){loads++}play(){plays++;this.paused=false;return Promise.resolve()}pause(){this.paused=true}}
const config={schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.22,duckGain:.055,fadeInMs:0,fadeOutMs:0,duckAttackMs:0,duckReleaseMs:0,loopStartSeconds:0,loopEndSeconds:null};
const document={addEventListener:(t,h)=>handlers[t]=h,removeEventListener(){}};const s={Audio,URL,location:{href:'https://example.test/'},document,fetch:async()=>({ok:true,json:async()=>config}),addEventListener:(t,h)=>handlers[t]=h,setTimeout,clearTimeout};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('ambient.js','utf8'),s);
(async()=>{const a=s.TombWorldAmbient,x=Audio.instance,near=(v,n)=>Math.abs(v-n)<1e-10;a.setVolumeMultiplier(.5);await a.init();a.setActive(true);await a.playFromGesture();if(!near(x.volume,.11))throw Error('normal scale');const before={plays,loads,time:x.currentTime};handlers.tombworldnarrationactivity({detail:{active:true}});if(!near(x.volume,.0275))throw Error('duck scale');a.setVolumeMultiplier(.25);if(!near(x.volume,.01375))throw Error('live duck scale');handlers.tombworldnarrationactivity({detail:{active:false}});if(!near(x.volume,.055))throw Error('scaled restore');if(plays!==before.plays||loads!==before.loads||x.currentTime!==before.time)throw Error('media restarted')})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_legacy_audio_guards_and_asset_precache(self):
        for forbidden in ("AudioContext", "webkitAudioContext"):
            self.assertNotIn(forbidden, AMBIENT)
        self.assertEqual(1, AMBIENT.count("new global.Audio()"))
        self.assertIn('"file": "Ambient/caverns.ogg"', (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        self.assertIn("await precacheAmbient(cache)", (ROOT / "service-worker.js").read_text())
        self.assertNotIn("click-sfx", APP.lower() + AMBIENT.lower() + NARRATION.lower())


if __name__ == "__main__":
    unittest.main()
