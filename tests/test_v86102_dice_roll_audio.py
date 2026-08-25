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
        self.assertGreaterEqual(tuple(map(int, CURRENT_APP_VERSION.split("."))), (8, 6, 102))
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

    def test_module_was_intentionally_migrated_from_html_audio(self):
        self.assertNotRegex(SFX, r"\bnew Audio\s*\(")
        self.assertIn("AudioContext", SFX)
        self.assertIn("webkitAudioContext", SFX)
        self.assertIn("createBufferSource()", SFX)
        self.assertIn("dice-roll-flem0527-750ms-50.mp3", SFX)

    def test_preference_master_volume_and_menu_are_independent(self):
        self.assertIn("tombWorldBattleGuide.diceRollEnabled", SFX)
        self.assertIn("localStorage.getItem(PREFERENCE_KEY) !== 'false'", SFX)
        self.assertIn("!masterEnabled || !preferenceEnabled", SFX)
        self.assertIn("if (!masterEnabled) stop();", SFX)
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
        self.assertIn("tombWorldBattleGuide.diceRollEnabled", fallback)
        self.assertIn("localStorage.getItem(preferenceKey)!=='false'", fallback)
        self.assertIn("localStorage.setItem(preferenceKey,String(preferenceEnabled))", fallback)
        self.assertIn("isPreferenceEnabled:()=>preferenceEnabled", fallback)
        self.assertIn("activateFromGesture:()=>Promise.resolve(false)", fallback)
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
        settle_combat_start = APP.index("function settleCombatDice")
        settle_combat_source = APP[settle_combat_start:APP.index("\n  function settleAnimatedDice", settle_combat_start)]
        settle_animated_start = APP.index("function settleAnimatedDice")
        settle_animated_source = APP[settle_animated_start:APP.index("\n  function ", settle_animated_start + 10)]
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
let attackRow=null,defenseRow=null;
const makeRow=animated=>({{classList:{{contains:value=>animated&&value==='animated-roll',replace:()=>{{}}}},innerHTML:''}});
const $=(selector,root)=>selector.includes('attack')?attackRow:defenseRow;
Object.defineProperty(container,'innerHTML',{{get(){{return this._html;}},set(value){{
  this._html=value;
  const attack=value.includes('Rolling after the attack');
  events.push(attack?'attack-animation':'defense-animation');
  attackRow=makeRow(attack); defenseRow=makeRow(!attack);
}}}});
{settle_combat_source}
{settle_animated_source}
{function_source}
runAutomaticCombatRolls({{container,profile:{{}},defenseSave:3,rolledAttackDice:[{{value:5}}],rolledDefenseDice:[{{value:4}}],onComplete:()=>events.push('complete')}});
if(events.join()!=='attack-animation,sfx'||typeof scheduled!=='function')process.exit(1);
scheduled();
if(events.join()!=='attack-animation,sfx,defense-animation,sfx'||typeof scheduled!=='function')process.exit(1);
scheduled();
if(events.join()!=='attack-animation,sfx,defense-animation,sfx,complete')process.exit(1);
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
