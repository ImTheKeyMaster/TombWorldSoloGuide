import hashlib
import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
SFX = (ROOT / "dice-sfx.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class DiceWebAudioReleaseTests(unittest.TestCase):
    def test_release_asset_offline_and_save_version(self):
        self.assertEqual((8, 6, 103), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        asset = ROOT / "Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3"
        self.assertEqual(
            "30b23dd163cfdbeaa4cbc436e5ce436e576c88fd41ed980ed8514dabcb953e40",
            hashlib.sha256(asset.read_bytes()).hexdigest(),
        )
        self.assertIn("'./Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3'", WORKER)
        self.assertIn(f"dice-sfx.js?v={CURRENT_APP_VERSION}", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_isolated_web_audio_architecture(self):
        self.assertNotRegex(SFX, r"\bnew\s+Audio\s*\(")
        self.assertIn("window.AudioContext || window.webkitAudioContext", SFX)
        self.assertEqual(1, SFX.count("new AudioContextConstructor()"))
        self.assertEqual(1, SFX.count("decodeAudioData(data)"))
        self.assertIn("createBufferSource()", SFX)
        self.assertIn("createGain()", SFX)
        self.assertIn("const activeSources = new Set()", SFX)
        for forbidden in ("TombWorldNarration", "TombWorldAmbient", "MediaElementAudioSourceNode", "currentTime", "playbackRequest", "eventQueue", "deadlyEncounterQueue", "desiredActive", "duck"):
            self.assertNotIn(forbidden, SFX)

    def test_early_initialization_and_silent_gesture_activation(self):
        self.assertIn("void TombWorldDiceSfx.init();", APP)
        self.assertIn("TombWorldDiceSfx?.activateFromGesture?.()", APP)
        activation = SFX[SFX.index("function activateFromGesture") : SFX.index("function setPreferenceEnabled")]
        self.assertIn("context.resume()", activation)
        self.assertNotIn("startSource", activation)

    def test_attack_and_defense_request_audio_in_the_animation_transition(self):
        automatic = APP[APP.index("function runAutomaticCombatRolls") : APP.index("function retainedDiceTotals")]
        attack_render = automatic.index("container.innerHTML=")
        attack_start = automatic.index("void TombWorldDiceSfx.play()")
        defense_render = automatic.index("container.innerHTML=", attack_render + 1)
        settle_call = automatic.index("timer=settleCombatDice", defense_render)
        self.assertLess(attack_render, attack_start)
        self.assertLess(defense_render, settle_call)
        settle = APP[APP.index("function settleAnimatedDice") : APP.index("function projectedNpoWounds")]
        self.assertLess(settle.index("classList.contains('animated-roll')"), settle.index("void TombWorldDiceSfx.play()"))
        self.assertLess(settle.index("void TombWorldDiceSfx.play()"), settle.index("setTimeout"))

    def test_runtime_buffer_reuse_overlap_gain_master_toggle_stop_and_failures(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
let fetches=0,decodes=0,resumes=0,stored=null;
const sources=[];
class Source {{
  constructor(){{this.stopped=false;sources.push(this)}}
  connect(){{}} start(){{if(Source.throwStart)throw Error('start');this.started=true}} stop(){{this.stopped=true}};
}}
class Context {{
  constructor(){{this.state='suspended';this.destination={{}};Context.instances++}}
  createGain(){{return {{gain:{{value:1}},connect(){{}}}}}}
  createBufferSource(){{return new Source()}}
  decodeAudioData(){{decodes++;return Context.decodeFails?Promise.reject(Error('decode')):Promise.resolve({{buffer:true}})}}
  resume(){{resumes++;if(Context.resumeFails)return Promise.reject(Error('resume'));this.state='running';return Promise.resolve()}}
}}
Context.instances=0;
const context={{Promise,Set,fetch:()=>{{fetches++;return Context.fetchFails?Promise.reject(Error('fetch')):Promise.resolve({{ok:true,arrayBuffer:()=>Promise.resolve(new ArrayBuffer(1))}})}},localStorage:{{getItem:()=>stored,setItem:(_,v)=>stored=v}},window:{{AudioContext:Context}}}};
Object.assign(context.window,{{window:context.window,fetch:context.fetch,localStorage:context.localStorage}});
vm.runInNewContext(fs.readFileSync({str(ROOT / 'dice-sfx.js')!r},'utf8'),context);
const s=context.window.TombWorldDiceSfx;
(async()=>{{
  if(!await s.init()||Context.instances!==1||fetches!==1||decodes!==1)process.exit(1);
  if(!await s.activateFromGesture()||sources.length!==0||resumes!==1)process.exit(2);
  if(!await s.play()||!await s.play()||sources.length!==2||fetches!==1||decodes!==1)process.exit(3);
  s.setVolumeMultiplier(.25);
  s.setMasterEnabled(false);
  if(!sources.every(x=>x.stopped)||await s.play())process.exit(4);
  s.setMasterEnabled(true);s.setPreferenceEnabled(false);if(await s.play())process.exit(5);
  s.setPreferenceEnabled(true);if(!await s.play()||Context.instances!==1||fetches!==1)process.exit(6);
  Source.throwStart=true;if(await s.play())process.exit(7);Source.throwStart=false;
  context.window.AudioContext.prototype.state='suspended';
  context.window.TombWorldDiceSfx.stop();
}})().catch(()=>process.exit(8));
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    def test_resume_failure_is_nonfatal(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
class C{{constructor(){{this.state='suspended';this.destination={{}}}}createGain(){{return{{gain:{{}},connect(){{}}}}}}resume(){{return Promise.reject(Error('blocked'))}}}}
const context={{Promise,Set,fetch:()=>Promise.reject(Error('offline')),localStorage:{{getItem:()=>null,setItem(){{}}}},window:{{AudioContext:C}}}};Object.assign(context.window,{{window:context.window,fetch:context.fetch,localStorage:context.localStorage}});
vm.runInNewContext(fs.readFileSync({str(ROOT / 'dice-sfx.js')!r},'utf8'),context);
(async()=>{{if(await context.window.TombWorldDiceSfx.play()!==false)process.exit(1)}})().catch(()=>process.exit(2));
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    def test_fetch_and_decode_failures_are_nonfatal_and_retryable(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync({str(ROOT / 'dice-sfx.js')!r},'utf8');
async function scenario(failure){{
  let fetches=0,decodes=0,fail=true;
  class C{{
    constructor(){{this.state='running';this.destination={{}}}}
    createGain(){{return{{gain:{{value:1}},connect(){{}}}}}}
    createBufferSource(){{return{{connect(){{}},start(){{}}}}}}
    decodeAudioData(){{decodes++;return failure==='decode'&&fail?Promise.reject(Error('decode')):Promise.resolve({{buffer:true}})}}
  }}
  const fetch=()=>{{fetches++;if(failure==='fetch-sync'&&fail)throw Error('fetch');if(failure==='fetch'&&fail)return Promise.reject(Error('fetch'));return Promise.resolve({{ok:true,arrayBuffer:()=>Promise.resolve(new ArrayBuffer(1))}})}};
  const context={{Promise,Set,fetch,localStorage:{{getItem:()=>null,setItem(){{}}}},window:{{AudioContext:C}}}};
  Object.assign(context.window,{{window:context.window,fetch,localStorage:context.localStorage}});
  vm.runInNewContext(source,context);
  const s=context.window.TombWorldDiceSfx;
  if(await s.init())throw Error(failure+' unexpectedly initialized');
  fail=false;
  if(!await s.play())throw Error(failure+' did not retry');
  if(fetches!==2)throw Error(failure+' fetch count '+fetches);
  if(decodes!==(failure==='decode'?2:1))throw Error(failure+' decode count '+decodes);
}}
(async()=>{{for(const failure of ['fetch-sync','fetch','decode'])await scenario(failure)}})().catch(error=>{{console.error(error);process.exit(1)}});
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
