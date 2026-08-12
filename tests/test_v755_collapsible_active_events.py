import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
ENGINE = (ROOT / "event-effects.js").read_text()
INDEX = (ROOT / "index.html").read_text()
STYLES = (ROOT / "styles.css").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def function_source(name, next_name):
    return APP.split(f"function {name}(", 1)[1].split(f"function {next_name}(", 1)[0]


def run_engine(expression):
    script = f"const e=require('./event-effects.js'); process.stdout.write(JSON.stringify({expression}));"
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def state(*definition_ids, turning_point=2):
    return {"turningPoint": turning_point, "eventState": {"active": [
        {"definitionId": definition_id, "startedTurningPoint": turning_point,
         "expiresAfterTurningPoint": turning_point} for definition_id in definition_ids
    ]}}


class CollapsibleActiveEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.component = function_source("activeEventEffectsHtml", "tombWorldEventActive")
        cls.render_play = function_source("renderPlay", "activeEventEffectsHtml")

    def test_01_no_events_render_no_panel_or_details(self):
        self.assertIn("if(!active.length)return ''", self.component)
        self.assertLess(self.component.index("if(!active.length)return ''"), self.component.index("<details"))

    def test_02_03_singular_and_plural_headings(self):
        self.assertIn("active.length===1?'EVENT':'EVENTS'", self.component)
        self.assertIn("ACTIVE TOMB WORLD ${", self.component)

    def test_04_active_count_is_visible_and_accessible(self):
        self.assertIn('class="active-events-count">${active.length} ACTIVE', self.component)
        self.assertIn('aria-label="${active.length===1?', self.component)
        self.assertIn('${active.length} active', self.component)

    def test_05_06_07_native_details_is_collapsed_by_default(self):
        details = re.search(r'<details class="active-events-details"([^>]*)>', self.component)
        self.assertIsNotNone(details)
        self.assertNotRegex(details.group(1), r'\bopen\b')
        self.assertIn('<summary class="active-events-summary"', self.component)

    def test_08_titles_and_descriptions_are_expandable_and_escaped(self):
        content_start = self.component.index('<div class="active-events-content">')
        content = self.component[content_start:]
        self.assertIn('escapeHtml(event.title)', content)
        self.assertIn('escapeHtml(event.text)', content)
        self.assertLess(content.index('active.map(event=>'), content.index('escapeHtml(event.title)'))

    def test_09_existing_event_order_is_preserved(self):
        self.assertIn("active.map(event=>", self.component)
        self.assertNotIn(".sort(", self.component)
        self.assertNotIn(".reverse(", self.component)

    def test_10_component_is_used_for_all_non_strategy_play_screens(self):
        self.assertIn("state.phase!=='strategy'?activeEventEffectsHtml():''", self.render_play)
        self.assertIn("state.phase==='firefight'?activationTracker():''", self.render_play)
        self.assertIn("state.phase==='end'", function_source("nextStepCard", "missionStrategyPending"))
        self.assertIn("state.phase==='between'", function_source("nextStepCard", "missionStrategyPending"))

    def test_11_player_and_npo_activation_cards_follow_the_component(self):
        next_step = function_source("nextStepCard", "missionStrategyPending")
        self.assertIn('<h2>Player Activation</h2>', next_step)
        self.assertIn('<h2 class="npo-activation-title">NPO Activation</h2>', next_step)
        self.assertLess(self.render_play.index("activeEventEffectsHtml()"), self.render_play.index("nextStepCard()"))

    def test_12_strategy_phase_keeps_its_resolution_cards(self):
        self.assertIn("state.phase!=='strategy'?activeEventEffectsHtml():''", self.render_play)
        strategy = function_source("strategyCard", "bindPlay")
        self.assertIn("strategyEventsStepHtml", strategy)
        self.assertIn("function strategyEventHtml", strategy)
        self.assertIn('tomb-world-event-card', APP)

    def test_13_collapsed_presentation_does_not_control_event_lookup(self):
        lookup = function_source("tombWorldEventActive", "nextStepCard")
        self.assertIn("EventEffects.activeRecords(state,state.turningPoint)", lookup)
        self.assertNotIn("active-events-details", lookup)
        self.assertNotIn("open", lookup)

    def test_14_countertemporal_shifting_remains_active(self):
        s = json.dumps(state("countertemporal-shifting"))
        packets = run_engine(f"e.resolveCountertemporalPackets({s},[{{damage:3}}],{{turningPoint:2,attackerSide:'player',defenderSide:'npo',attackType:'shoot',rollD6:()=>5}})")
        self.assertEqual(packets[0]["finalDamage"], 2)

    def test_15_reanimation_protocols_remains_active(self):
        s = json.dumps(state("reanimation-protocols"))
        result = run_engine(f"e.resolveNpoIncapacitation({s},{{turningPoint:2,npoId:'n1',eventAttempts:{{}},candidates:[]}})")
        self.assertEqual(result["candidates"][0]["sourceId"], "tomb-world-event:reanimation-protocols")

    def test_16_dark_of_the_tomb_remains_active(self):
        s = json.dumps(state("dark-of-the-tomb"))
        result = run_engine(f"e.effectiveAttackRerolls({s},{{turningPoint:2,attackerSide:'player',attackType:'shoot',moreThanEight:true}})")
        self.assertFalse(result["attackDice"])

    def test_17_my_will_be_done_remains_active(self):
        s = json.dumps(state("my-will-be-done"))
        result = run_engine(f"e.effectiveWeaponProfile({s},{{hit:4,rules:[]}},{{turningPoint:2,attackerSide:'npo',sameRoomAsC1:true}})")
        self.assertEqual(result["accurate"], 1)
        self.assertIn("Accurate 1", result["rules"])

    def test_18_event_expiry_is_unchanged(self):
        expired = state("dark-of-the-tomb")
        expired["eventState"]["active"][0]["expiresAfterTurningPoint"] = 1
        self.assertEqual(run_engine(f"e.activeRecords({json.dumps(expired)},2)"), [])
        self.assertIn("expiresAfterTurningPoint!==state.turningPoint", APP)

    def test_19_other_details_styles_are_unchanged_and_css_is_scoped(self):
        self.assertIn(".help-list details", STYLES)
        self.assertIn(".activation-details summary", STYLES)
        self.assertNotIn("\ndetails{", STYLES)
        self.assertNotIn("\nsummary{", STYLES)
        for selector in (".active-events-panel", ".active-events-details", ".active-events-summary",
                         ".active-events-count", ".active-events-content"):
            self.assertIn(selector, STYLES if selector != ".active-events-details" else self.component + STYLES)

    def test_20_summary_is_touch_friendly_wraps_and_has_a_chevron(self):
        self.assertIn("min-height:44px", STYLES)
        self.assertIn("flex-wrap:wrap", STYLES)
        self.assertIn(".active-events-summary::after", STYLES)
        self.assertIn(".active-events-details[open] .active-events-summary::after", STYLES)

    def test_21_application_displays_version_755(self):
        self.assertIn("const APP_VERSION = '8.6.57';", APP)
        self.assertIn("const APP_VERSION = '8.6.57';", WORKER)
        self.assertIn("V8.6.57", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.57"))
        self.assertIn("## v8.6.25", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.57", INDEX)

    def test_22_save_version_and_event_engine_are_not_changed_by_component(self):
        self.assertNotIn("SAVE_VERSION", self.component)
        self.assertNotIn("localStorage", self.component)
        self.assertIn("function activeRecords", ENGINE)


if __name__ == "__main__":
    unittest.main()
