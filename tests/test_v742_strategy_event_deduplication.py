import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
STRATEGY_HELPERS = APP.split("function strategyEventPresentation", 1)[1].split("function strategyCard", 1)[0]
STRATEGY_CARD = APP.split("function strategyCard", 1)[1].split("function strategyEventHtml", 1)[0]
EVENT_HTML = APP.split("function strategyEventHtml", 1)[1].split("function activationTracker", 1)[0]


def render_strategy(events, active, required=1, normal=0):
    event_index = next((index for index, item in enumerate(events) if item['status'] == 'drawn'), len(events))
    script = f"""
const state={{turningPoint:2,phase:'strategy',strategyStage:'summary',threat:0,
  strategyData:{{viewStep:'events',eventRequirementTurningPoint:2,requiredEventCount:{required},normalEventCount:{normal},events:{json.dumps(events)},eventIndex:{event_index},eventPending:false}},
  eventState:{{active:{json.dumps(active)},transactions:{{}}}},reinforcementState:{{status:'idle',operativeIds:[],blockedOperativeIds:[]}},roster:[]}};
const window={{matchMedia:()=>({{matches:true}})}};
const escapeHtml=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const sortedNposForDisplay=items=>items;
const ceaselessScuttlingEligible=()=>false;
const factionGuidanceHtml=()=>'';
const missionStrategyPromptHtml=()=>'';
const missionStrategyPending=()=>false;
const npoName=n=>n.name;
const npoDefinition=()=>({{}});
const npoWeapon=()=>null;
const threatGrade=()=>0;
const readyNpos=()=>[];
function strategyEventPresentation{STRATEGY_HELPERS}
function strategyCard{STRATEGY_CARD}
function strategyEventHtml{EVENT_HTML}
process.stdout.write(strategyCard());
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def event(instance, definition, title, text, status="resolved", result="Complete"):
    return {"instanceId": instance, "definitionId": definition, "type": "tomb-world-event",
            "title": title, "text": text, "execution": {"type": "activate"},
            "duration": "turning-point", "status": status, "result": result}


class StrategyEventDeduplicationTests(unittest.TestCase):
    def setUp(self):
        self.effect = "Until the end of the turning point, ignore damage on a 5+."
        self.resolved = event("counter-1", "countertemporal-shifting", "Countertemporal Shifting",
                              self.effect, result="Effect active until the end of this Turning Point.")
        self.active = {**self.resolved, "status": "active", "startedTurningPoint": 2,
                       "expiresAfterTurningPoint": 2}

    def test_matched_persistent_event_renders_once_without_duplicate_section(self):
        html = render_strategy([self.resolved], [self.active])
        self.assertEqual(html.count(self.effect), 1)
        self.assertEqual(html.count("Countertemporal Shifting"), 1)
        self.assertNotIn("Active event effects", html)
        self.assertNotIn("Other Active Event Effects", html)
        self.assertIn("RESOLVED • ACTIVE", html)
        self.assertIn("Effect active until the end of this Turning Point.", html)
        self.assertNotIn("Current Battlefield State", html)

    def test_statuses_are_derived_without_mutating_canonical_records(self):
        immediate = event("metal-1", "living-metal-flux", "Living Metal Flux", "Regain wounds.")
        pending = event("warrior-1", "awakened-warrior", "Awakened Warrior", "Place a Warrior.", "drawn")
        redrawn = event("maze-1", "maze-reforms", "The Maze Reforms", "Change terrain.", "redrawn")
        html = render_strategy([immediate, pending, redrawn], [], required=2, normal=2)
        self.assertIn(">RESOLVED<", html)
        self.assertIn(">PENDING<", html)
        self.assertIn(">REDRAWN<", html)
        self.assertNotIn("RESOLVED • ACTIVE", html)
        self.assertEqual(immediate["status"], "resolved")
        self.assertIn("event.status==='resolved'?strategyEventActiveEffect", EVENT_HTML)
        self.assertNotIn("event.status='active'", EVENT_HTML)

    def test_matching_prefers_instance_id_and_never_uses_title(self):
        same_title_wrong_instance = {**self.active, "instanceId": "counter-2"}
        html = render_strategy([self.resolved], [same_title_wrong_instance])
        self.assertNotIn("RESOLVED • ACTIVE", html)
        self.assertIn("Other Active Event Effects", html)
        helper = "function strategyEventActiveEffect" + STRATEGY_HELPERS.split("function strategyEventActiveEffect", 1)[1].split("function strategyEventSummary", 1)[0]
        self.assertIn("event.instanceId===active.instanceId", helper)
        self.assertIn("event.definitionId===active.definitionId", helper)
        self.assertNotIn("title", helper)

    def test_unmatched_and_mixed_restored_effects_use_compact_fallback(self):
        legacy = {"definitionId": "my-will-be-done", "title": "My Will Be Done",
                  "text": "Improve NPO Hit.", "status": "active", "expiresAfterTurningPoint": 2}
        html = render_strategy([self.resolved], [self.active, legacy])
        fallback = html.split("Other Active Event Effects", 1)[1]
        self.assertIn("My Will Be Done", fallback)
        self.assertNotIn("Countertemporal Shifting", fallback)
        self.assertEqual(html.count(self.effect), 1)
        self.assertEqual(render_strategy([self.resolved], [self.active]).count("Other Active Event Effects"), 0)

    def test_summary_singular_plural_and_redraw_chain(self):
        redrawn = event("maze-1", "maze-reforms", "The Maze Reforms", "Change terrain.", "redrawn")
        one = render_strategy([self.resolved], [self.active])
        chain = render_strategy([redrawn, self.resolved], [self.active])
        zero = render_strategy([], [], required=0)
        self.assertIn("1 required • 1 card drawn • 1 resolved", one)
        self.assertIn('aria-label="1 event required, 1 event card drawn, 1 event resolved"', one)
        self.assertIn("1 required • 2 cards drawn • 1 resolved", chain)
        self.assertIn('aria-label="1 event required, 2 event cards drawn, 1 event resolved"', chain)
        self.assertLess(chain.index("The Maze Reforms"), chain.index("Countertemporal Shifting"))
        self.assertEqual(chain.count("RESOLVED • ACTIVE"), 1)
        summary = "function strategyEventSummary" + STRATEGY_HELPERS.split("function strategyEventSummary", 1)[1]
        self.assertIn("cardsDrawn===1?'card':'cards'", summary)
        self.assertIn("0 required • 0 cards drawn • 0 resolved", subprocess.run(
            ["node", "-e", f"const state={{eventState:{{active:[]}}}}; function strategyEventPresentation{STRATEGY_HELPERS}; console.log(strategyEventSummary({{required:0,cardsDrawn:0,resolved:0}}).visible)"],
            cwd=ROOT, text=True, capture_output=True, check=True).stdout)
        self.assertIn("No Tomb World Event", zero)

    def test_lifecycle_persistence_and_later_reminders_remain_unchanged(self):
        later = APP.split("function activeEventEffectsHtml", 1)[1].split("function nextStepCard", 1)[0]
        expiry = APP.split("$('#finishTp')", 1)[1].split("function showCeaselessScuttling", 1)[0]
        resolution = APP.split("function beginCurrentEvent", 1)[1].split("function completeCurrentEvent", 1)[0]
        normalization = APP.split("const importedEvents=", 1)[1].split("const livingImportedPlayers", 1)[0]
        self.assertIn("state.eventState.active||[]", later)
        self.assertIn("event.title", later)
        self.assertIn("event.text", later)
        self.assertIn("completeTurningPointCleanup()", expiry)
        self.assertIn("expiresAfterTurningPoint!==state.turningPoint", APP)
        self.assertIn("state.eventState.active.push({...event", resolution)
        self.assertIn("const normalizedActive=Array.isArray(importedEvents.active)", normalization)
        self.assertNotIn("state.eventState.active=", STRATEGY_CARD)

    def test_rules_and_release_regressions(self):
        counts = APP.split("function normalStrategyEventCount", 1)[1].split("function threatLabel", 1)[0]
        self.assertIn("return suggestedInitiative==='npo'||threat===15?2:1", counts)
        self.assertIn("Math.max(normalCount,1)", counts)
        self.assertIn("1 event required by Restless Tomb.", render_strategy([self.resolved], [self.active]))
        self.assertIn("ACTIVE TOMB WORLD", APP.split("function activeEventEffectsHtml", 1)[1].split("function nextStepCard", 1)[0])
        self.assertIn("const APP_VERSION = '8.6.41';", APP)
        self.assertIn("const APP_VERSION = '8.6.41';", WORKER)
        self.assertIn("V8.6.41", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.41"))
        self.assertIn("## v8.6.25", README)
        self.assertNotIn("portrait", EVENT_HTML.lower())
        self.assertNotIn("obelisk", EVENT_HTML.lower())


if __name__ == "__main__":
    unittest.main()
