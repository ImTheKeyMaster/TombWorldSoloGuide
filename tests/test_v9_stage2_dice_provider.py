import re
import json
import subprocess
import unittest
from pathlib import Path
from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
STYLES = (ROOT / "styles.css").read_text()


def run_node(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class Stage2DiceProviderTests(unittest.TestCase):
    def test_dedicated_accessible_dialog_has_required_controls(self):
        self.assertIn('<dialog id="diceEntryDialog"', INDEX)
        self.assertIn('aria-labelledby="diceEntryTitle"', INDEX)
        self.assertIn('aria-describedby="diceEntryInstruction"', INDEX)
        self.assertIn('aria-live="polite"', INDEX)
        self.assertIn('id="diceEntryUndo" type="button" disabled>Undo', INDEX)
        self.assertIn('id="diceEntryCommit" type="button" disabled>Commit Results', INDEX)
        self.assertLess(INDEX.index('diceEntryTitle'), INDEX.index('diceEntryInstruction'))
        self.assertLess(INDEX.index('diceEntryInstruction'), INDEX.index('diceEntryResults'))
        self.assertLess(INDEX.index('diceEntryResults'), INDEX.index('diceEntryProgress'))
        self.assertLess(INDEX.index('diceEntryProgress'), INDEX.index('diceEntryKeypad'))

    def test_provider_validates_and_selects_source_centrally(self):
        validation = APP[APP.index("function validateDiceRequest") : APP.index("function renderManualDiceEntry")]
        self.assertIn("Number.isInteger(count)", validation)
        self.assertIn("count<=0", validation)
        self.assertIn("Number.isInteger(sides)", validation)
        self.assertIn("sides<2||sides>6", validation)
        provider = APP[APP.index("async function requestDiceResults") : APP.index("diceEntryUndo.addEventListener")]
        self.assertIn("if(!isPvpMode())return rollDice(validatedRequest.count,validatedRequest.sides)", provider)
        self.assertIn("return requestManualDiceResults(validatedRequest)", provider)
        self.assertIn("window.TombWorldDiceProvider=Object.freeze({requestDiceResults})", APP)

    def test_manual_entry_is_raw_immediate_and_ordered(self):
        render = APP[APP.index("function renderManualDiceEntry") : APP.index("function requestManualDiceResults")]
        self.assertIn("active.values.push(value)", render)
        self.assertIn("active.values.pop()", render)
        self.assertIn("active.values.slice()", render)
        self.assertIn("dieHtml({value,ariaLabel:`Die ${index+1}: ${value}`})", render)
        for interpretation in ("crit", "hit", "miss", "damage", "save", "TombWorldDiceSfx", "settleAnimatedDice"):
            self.assertNotIn(interpretation, render)

    def test_progress_limits_undo_commit_and_exactly_once_guards(self):
        render = APP[APP.index("function renderManualDiceEntry") : APP.index("function requestManualDiceResults")]
        self.assertIn("active.values.length===active.request.count", render)
        self.assertIn("active.values.length} of ${active.request.count} entered", render)
        self.assertIn("diceEntryUndo.disabled=active.values.length===0||active.committed", render)
        self.assertIn("diceEntryCommit.disabled=!complete||active.committed", render)
        self.assertIn("button.disabled=complete||active.committed", render)
        self.assertIn("active.values.length>=active.request.count", render)
        self.assertIn("if(!active||active.committed||active.values.length!==active.request.count)return false", render)
        self.assertLess(render.index("active.committed=true"), render.index("resolve(results)"))
        self.assertIn("activeManualDiceRequest=null", render)

    def test_keypad_supports_d3_d6_touch_and_keyboard_without_audio(self):
        manual = APP[APP.index("function requestManualDiceResults") : APP.index("async function requestDiceResults")]
        keyboard = APP[APP.index("diceEntryDialog.addEventListener('keydown'") : APP.index("window.TombWorldDiceProvider")]
        self.assertIn("Array.from({length:request.sides}", manual)
        self.assertIn('type="button" data-die-value=', manual)
        self.assertIn('aria-label="Enter ${value}"', manual)
        self.assertIn("button.onclick=()=>enterManualDie", manual)
        self.assertIn("event.key==='Backspace'", keyboard)
        self.assertIn("event.key==='Enter'", keyboard)
        enter_handler = keyboard[keyboard.index("else if(event.key==='Enter')") :]
        self.assertLess(enter_handler.index("event.preventDefault()"), enter_handler.index("if(!diceEntryCommit.disabled)"))
        self.assertNotIn("roll(", manual)
        self.assertNotIn("rollDice(", manual)
        self.assertNotIn("TombWorldDiceSfx", manual)

    def test_provider_and_manual_controls_execute_as_one_transaction(self):
        provider_source = APP[APP.index("let activeManualDiceRequest=null;") : APP.index("window.TombWorldDiceProvider")]
        result = run_node(f"""
const makeElement=()=>({{textContent:'',innerHTML:'',hidden:false,disabled:false,open:false,isConnected:true,listeners:{{}},
  addEventListener(name,handler){{this.listeners[name]=handler;}},showModal(){{this.open=true;}},close(){{this.open=false;}},
  focus(){{activeElement=this;}},querySelector(){{return keypadButtons[0]||null;}}}});
let activeElement=makeElement(),randomCalls=0;
const document={{get activeElement(){{return activeElement;}}}};
const requestAnimationFrame=callback=>callback();
const state={{gameMode:'solo',wounds:7,threat:3,journal:['unchanged']}};
const isPvpMode=()=>state.gameMode==='pvp';
const rollDice=(count,sides)=>{{randomCalls++;return Array.from({{length:count}},(_,index)=>(index%sides)+1);}};
const dieHtml=die=>`<i aria-label="${{die.ariaLabel}}">${{die.value}}</i>`;
let keypadButtons=[];
const $$=(selector,root)=>selector==='button'||selector==='[data-die-value]'?keypadButtons:[];
const diceEntryDialog=makeElement(),diceEntryTitle=makeElement(),diceEntryRoller=makeElement(),diceEntryInstruction=makeElement();
const diceEntryResults=makeElement(),diceEntryProgress=makeElement(),diceEntryKeypad=makeElement(),diceEntryUndo=makeElement(),diceEntryCommit=makeElement();
Object.defineProperty(diceEntryKeypad,'innerHTML',{{set(html){{
  this._html=html; keypadButtons=[...html.matchAll(/data-die-value="(\\d+)"/g)].map(match=>{{const button=makeElement();button.dataset={{dieValue:match[1]}};return button;}});
}},get(){{return this._html;}}}});
{provider_source}
(async()=>{{
  const solo=await requestDiceResults({{count:4,sides:6}});
  state.gameMode='pvp';
  const snapshot=JSON.stringify(state);
  const pending=requestDiceResults({{count:4,sides:6,title:'Attack Roll',rollerLabel:'Deathwatch'}});
  const concurrentRejected=await requestDiceResults({{count:1,sides:3}}).then(()=>false,error=>error.message.includes('already active'));
  [6,3,4,1].forEach(value=>keypadButtons[value-1].onclick());
  const afterEntry={{progress:diceEntryProgress.textContent,commitDisabled:diceEntryCommit.disabled,keypadDisabled:keypadButtons.every(button=>button.disabled),
    dice:diceEntryResults.innerHTML,stateUnchanged:JSON.stringify(state)===snapshot,randomCalls}};
  diceEntryUndo.listeners.click();
  const afterUndo={{progress:diceEntryProgress.textContent,commitDisabled:diceEntryCommit.disabled,keypadEnabled:keypadButtons.every(button=>!button.disabled)}};
  keypadButtons[0].onclick();
  diceEntryCommit.listeners.click(); diceEntryCommit.listeners.click();
  const manual=await pending;
  process.stdout.write(JSON.stringify({{solo,manual,concurrentRejected,afterEntry,afterUndo,dialogOpen:diceEntryDialog.open,randomCalls}}));
}})();
""")
        self.assertEqual(result["solo"], [1, 2, 3, 4])
        self.assertEqual(result["manual"], [6, 3, 4, 1])
        self.assertTrue(result["concurrentRejected"])
        self.assertEqual(result["afterEntry"]["progress"], "4 of 4 entered")
        self.assertFalse(result["afterEntry"]["commitDisabled"])
        self.assertTrue(result["afterEntry"]["keypadDisabled"])
        self.assertIn('Die 1: 6', result["afterEntry"]["dice"])
        self.assertTrue(result["afterEntry"]["stateUnchanged"])
        self.assertEqual(result["afterEntry"]["randomCalls"], 1)
        self.assertEqual(result["afterUndo"], {"progress": "3 of 4 entered", "commitDisabled": True, "keypadEnabled": True})
        self.assertFalse(result["dialogOpen"])
        self.assertEqual(result["randomCalls"], 1)

    def test_concurrency_required_dialog_and_focus_are_protected(self):
        manual = APP[APP.index("function requestManualDiceResults") : APP.index("async function requestDiceResults")]
        self.assertIn("if(activeManualDiceRequest)return Promise.reject", manual)
        self.assertIn("catch(error){activeManualDiceRequest=null;throw error;}", manual)
        self.assertIn("diceEntryDialog.showModal()", manual)
        self.assertIn("returnFocus:document.activeElement", manual)
        self.assertIn("querySelector('button')?.focus", manual)
        self.assertIn("diceEntryDialog.addEventListener('cancel',event=>event.preventDefault())", APP)
        self.assertIn("returnFocus?.isConnected", APP)
        self.assertNotIn("diceEntryDialog.close()", APP[APP.index("function requestManualDiceResults") :])
        self.assertIn("diceEntryDialog.close()", APP[APP.index("function commitManualDiceResults") : APP.index("function requestManualDiceResults")])

    def test_dice_dialog_stacks_without_replacing_application_modal(self):
        self.assertIn('<dialog id="modal" class="modal"', INDEX)
        self.assertIn('<dialog id="diceEntryDialog" class="modal dice-entry-dialog"', INDEX)
        manual = APP[APP.index("function requestManualDiceResults") : APP.index("async function requestDiceResults")]
        self.assertNotIn("\n    showModal(", manual)
        self.assertNotIn("closeModal(", manual)
        self.assertNotIn("modalBody", manual)
        self.assertIn("diceEntryDialog.showModal()", manual)

    def test_manual_request_is_transient_and_existing_gameplay_is_not_routed(self):
        initial_state = APP[APP.index("const initialState") : APP.index("const loadedSave")]
        self.assertNotIn("dice", initial_state.lower())
        self.assertEqual(APP.count("async function requestDiceResults"), 1)
        before_provider, after_provider = APP.split("async function requestDiceResults", 1)
        self.assertNotIn("requestDiceResults(", before_provider)
        self.assertNotIn("requestDiceResults(", after_provider)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)

    def test_mobile_layout_wraps_and_keeps_large_touch_targets(self):
        self.assertIn(".dice-entry-results{min-height:44px", STYLES)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", STYLES)
        self.assertIn("min-height:52px", STYLES)
        self.assertIn("touch-action:manipulation", STYLES)
        self.assertIn("max-height:calc(100dvh - 20px)", STYLES)
        self.assertIn("calc(18px + env(safe-area-inset-bottom))", STYLES)
        self.assertRegex(STYLES.replace(" ", ""), re.compile(r"@media\(max-width:390px\).*?\.dice-entry-dialog", re.S))


if __name__ == "__main__":
    unittest.main()
