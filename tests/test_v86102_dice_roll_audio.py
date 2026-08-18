import hashlib
import re
import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SFX = (ROOT / "dice-sfx.js").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class DiceRollAudioReleaseTests(unittest.TestCase):
    def test_release_asset_and_offline_wiring(self):
        self.assertEqual((8, 6, 102), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        asset = ROOT / "Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3"
        self.assertTrue(asset.is_file())
        self.assertGreater(asset.stat().st_size, 0)
        self.assertEqual(
            "30b23dd163cfdbeaa4cbc436e5ce436e576c88fd41ed980ed8514dabcb953e40",
            hashlib.sha256(asset.read_bytes()).hexdigest(),
        )
        self.assertIn("'./Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3'", WORKER)
        self.assertIn(f'dice-sfx.js?v={CURRENT_APP_VERSION}', INDEX)
        self.assertLess(INDEX.index("dice-sfx.js"), INDEX.index("app.js"))
        runtime = "\n".join((APP, INDEX, SFX, WORKER))
        self.assertNotIn("dice-roll-flem0527-750ms.mp3", runtime)
        self.assertNotIn("Btn_Click.wav", runtime)
        self.assertFalse((ROOT / "Assets/Audio/Narration/SFX/sfx-config.json").exists())

    def test_module_uses_two_persistent_html_audio_elements(self):
        self.assertEqual(2, len(re.findall(r"\bnew Audio\s*\(", SFX)))
        self.assertIn("audio.preload = 'auto'", SFX)
        self.assertNotIn("cloneNode", SFX)
        self.assertIn("dice-roll-flem0527-750ms-50.mp3", SFX)
        for forbidden in ("AudioContext", "webkitAudioContext", "GainNode", "MediaElementAudioSourceNode"):
            self.assertNotIn(forbidden, SFX)
        play_body = SFX[SFX.index("function play()") : SFX.index("function setPreferenceEnabled")]
        self.assertNotIn("new Audio", play_body)
        self.assertIn("audio.currentTime = 0", play_body)
        self.assertIn(".catch(() => false)", play_body)

    def test_preference_master_volume_and_menu_are_independent(self):
        self.assertIn("tombWorldSoloGuide.diceRollEnabled", SFX)
        self.assertIn("localStorage.getItem(PREFERENCE_KEY) !== 'false'", SFX)
        self.assertIn("!masterEnabled || !preferenceEnabled", SFX)
        self.assertIn("if (!masterEnabled) stop();", SFX)
        self.assertIn("supportsInAppVolumeControl() === false", SFX)
        self.assertIn('id="diceRollToggle"', APP)
        self.assertIn('role="switch" aria-labelledby="diceRollLabel"', APP)
        handler = APP[APP.index("$('#diceRollToggle').onclick") : APP.index("const gameVolume")]
        self.assertIn("TombWorldDiceSfx.setPreferenceEnabled", handler)
        self.assertNotIn("TombWorldNarration.setPreferenceEnabled", handler)
        self.assertNotIn("ambientEnabled=", handler)
        self.assertNotIn("setGameAudioEnabled", handler)
        new_game = APP[APP.index("function startNewGameSetup") : APP.index("function confirmNewGame")]
        self.assertIn("TombWorldDiceSfx.stop()", new_game)
        self.assertNotIn("diceRollEnabled", new_game)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_module_does_not_touch_narration_or_ambient_lifecycle(self):
        for production_api in (
            "TombWorldNarration", "TombWorldAmbient", "tombworldnarrationactivity",
            "dispatchEvent", "addEventListener",
        ):
            self.assertNotIn(production_api, SFX)

    def test_app_fallback_keeps_the_menu_preference_functional(self):
        start = APP.index("function createDiceSfxFallback")
        fallback = APP[start : APP.index("const TombWorldDiceSfx", start)]
        self.assertIn("tombWorldSoloGuide.diceRollEnabled", fallback)
        self.assertIn("localStorage.getItem(preferenceKey)!=='false'", fallback)
        self.assertIn("localStorage.setItem(preferenceKey,String(preferenceEnabled))", fallback)
        self.assertIn("isPreferenceEnabled:()=>preferenceEnabled", fallback)
        self.assertIn("play:()=>Promise.resolve(false)", fallback)
        self.assertNotIn("Audio", fallback)

    def test_visible_rolls_share_750ms_timing_and_batch_triggers(self):
        self.assertIn("const DICE_ROLL_ANIMATION_MS = 750;", APP)
        self.assertNotRegex(APP, r"(?:,|\))700\)")
        self.assertIn("row?.classList.contains('animated-roll')&&dice.length", APP)
        for function_name in (
            "settleAnimatedDice", "showAggressiveDefenseResolution", "showHotResult",
            "runAutomaticCombatRolls", "animateMissionDice",
        ):
            start = APP.index(f"function {function_name}")
            next_function = APP.find("\n  function ", start + 10)
            body = APP[start : next_function if next_function >= 0 else None]
            self.assertIn("TombWorldDiceSfx.play()", body, function_name)
            self.assertIn("DICE_ROLL_ANIMATION_MS", body, function_name)
        automatic = APP[APP.index("function runAutomaticCombatRolls") : APP.index("function retainedDiceTotals")]
        self.assertEqual(2, automatic.count("TombWorldDiceSfx.play()") + automatic.count("settleCombatDice("))
        self.assertEqual(5, APP.count("void TombWorldDiceSfx.play()"))
        self.assertNotIn("await TombWorldDiceSfx.play()", APP)

    def test_attack_and_defense_start_audio_synchronously_with_each_animation(self):
        start = APP.index("function runAutomaticCombatRolls")
        end = APP.index("\n  function retainedDiceTotals", start)
        function_source = APP[start:end]
        script = f"""
const events=[];
let scheduled=null;
const container={{isConnected:true,_html:'',set innerHTML(value){{this._html=value;events.push(value.includes('Rolling after the attack')?'attack-animation':'defense-animation');}},get innerHTML(){{return this._html;}}}};
const TombWorldDiceSfx={{play:()=>{{events.push('sfx');return Promise.resolve(true);}}}};
const DICE_ROLL_ANIMATION_MS=750;
const setTimeout=(callback,delay)=>{{if(delay!==750)process.exit(1);scheduled=callback;return 1;}};
const clearTimeout=()=>{{}};
const applySevereToAttackDice=dice=>({{dice}});
const retainSuccessfulDice=dice=>dice;
const rolledAttackDiceForProfile=()=>[];
const rollingDieHtml=()=>'<i>rolling</i>';
const dieHtml=()=>'<i>settled</i>';
const effectiveDefenseDiceCount=()=>1;
const rolledCombatDice=()=>[{{value:4}}];
const automaticWeaponRuleMessages=()=>[];
const severeAppliedHtml=()=>'';
const escapeHtml=value=>value;
const settleCombatDice=(combat,onComplete)=>{{events.push('settle-called');void TombWorldDiceSfx.play();onComplete();return ()=>{{}};}};
{function_source}
runAutomaticCombatRolls({{container,profile:{{}},defenseSave:3,rolledAttackDice:[{{value:5}}],rolledDefenseDice:[{{value:4}}],onComplete:()=>events.push('complete')}});
if(events.join()!=='attack-animation,sfx'||typeof scheduled!=='function')process.exit(1);
scheduled();
if(events.join()!=='attack-animation,sfx,defense-animation,settle-called,sfx,complete')process.exit(1);
"""
        subprocess.run(["node", "-e", script], check=True, cwd=ROOT)

    def test_desktop_volume_updates_both_players(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
const players=[];
class FakeAudio {{
  constructor(){{this.volume=1;players.push(this);}}
  load(){{}} play(){{return Promise.resolve();}} pause(){{}}
}}
const context={{Audio:FakeAudio,Promise,localStorage:{{getItem:()=>null,setItem:()=>{{}}}},window:{{TombWorldAudioCapabilities:{{supportsInAppVolumeControl:()=>true}}}}}};
context.window.window=context.window; context.window.Audio=FakeAudio; context.window.localStorage=context.localStorage;
vm.runInNewContext(fs.readFileSync({str(ROOT / 'dice-sfx.js')!r},'utf8'),context);
context.window.TombWorldDiceSfx.setVolumeMultiplier(0.25);
if(players.length!==2||players.some(player=>player.volume!==0.25))process.exit(1);
"""
        subprocess.run(["node", "-e", script], check=True, cwd=ROOT)

    def test_playback_eligibility_and_rejection_are_retryable(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
let stored=null, instances=0, loads=0, plays=[], pauses=0, currentTimeWrites=0, diceAudio=[];
class FakeAudio {{
  constructor(){{this.id=instances++; diceAudio.push(this); this.src=''; this.preload='';}}
  load(){{loads++;}}
  play(){{plays.push(this.id); return Promise.reject(new Error('blocked'));}}
  pause(){{pauses++;}}
  set currentTime(value){{if(value!==0)process.exit(1); currentTimeWrites++;}}
}}
const narration={{src:'narration.mp3',currentTime:42,queue:['event'],pauses:0}};
const ambient={{src:'ambient.ogg',currentTime:17,pauses:0}};
const context={{Audio:FakeAudio,Promise,localStorage:{{getItem:()=>stored,setItem:(_,v)=>stored=v}},window:{{TombWorldAudioCapabilities:{{supportsInAppVolumeControl:()=>true}},TombWorldNarration:narration,TombWorldAmbient:ambient}}}};
context.window.window=context.window; context.window.Audio=FakeAudio; context.window.localStorage=context.localStorage;
vm.runInNewContext(fs.readFileSync({str(ROOT / 'dice-sfx.js')!r},'utf8'),context);
const s=context.window.TombWorldDiceSfx;
(async()=>{{
  await s.init();
  await s.play(); await s.play(); await s.play();
  s.setMasterEnabled(false); await s.play();
  s.setMasterEnabled(true); s.setPreferenceEnabled(false); await s.play();
  s.setPreferenceEnabled(true); await s.play(); s.stop();
  const audioSource='Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3';
  if(instances!==2||loads!==2||plays.join()!=='0,1,0,1'||stored!=='true'||pauses!==4||currentTimeWrites!==8)process.exit(1);
  if(diceAudio.some(audio=>audio.src!==audioSource||audio.preload!=='auto'))process.exit(1);
  if(!vm.runInNewContext('window.TombWorldDiceSfx',context)||context.window.TombWorldNarration!==narration||context.window.TombWorldAmbient!==ambient)process.exit(1);
  if(narration.src!=='narration.mp3'||narration.currentTime!==42||narration.queue.join()!=='event'||narration.pauses!==0)process.exit(1);
  if(ambient.src!=='ambient.ogg'||ambient.currentTime!==17||ambient.pauses!==0)process.exit(1);
}})();
"""
        subprocess.run(["node", "-e", script], check=True, cwd=ROOT)

    def test_apple_mobile_volume_is_left_at_the_source_level(self):
        script = f"""
const fs=require('fs'),vm=require('vm');
let audioInstances=0, volumeWrites=0;
class FakeAudio {{
  constructor(){{audioInstances++;}}
  load(){{}} play(){{return Promise.resolve();}} pause(){{}}
  set volume(value){{volumeWrites++;}} get volume(){{return 1;}}
}}
const context={{Audio:FakeAudio,Promise,localStorage:{{getItem:()=>null,setItem:()=>{{}}}},window:{{TombWorldAudioCapabilities:{{supportsInAppVolumeControl:()=>false}}}}}};
context.window.window=context.window; context.window.Audio=FakeAudio; context.window.localStorage=context.localStorage;
vm.runInNewContext(fs.readFileSync({str(ROOT / 'dice-sfx.js')!r},'utf8'),context);
const s=context.window.TombWorldDiceSfx;
s.setVolumeMultiplier(0.25); s.setVolumeMultiplier(0.75);
if(audioInstances!==2||volumeWrites!==0)process.exit(1);
"""
        subprocess.run(["node", "-e", script], check=True, cwd=ROOT)

    def test_fallback_preference_behavior_without_audio_module(self):
        start = APP.index("function createDiceSfxFallback")
        fallback = APP[start : APP.index("const TombWorldDiceSfx", start)]
        script = f"""
let stored=null;
const localStorage={{getItem:()=>stored,setItem:(_,value)=>{{stored=value;}}}};
{fallback}
(async()=>{{
  const first=createDiceSfxFallback();
  if(!first.isPreferenceEnabled()||await first.play())process.exit(1);
  first.setPreferenceEnabled(false);
  const restored=createDiceSfxFallback();
  if(restored.isPreferenceEnabled()||stored!=='false')process.exit(1);
}})();
"""
        subprocess.run(["node", "-e", script], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
