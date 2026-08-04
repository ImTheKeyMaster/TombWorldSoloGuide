import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
ENGINE = (ROOT / "event-effects.js").read_text()
INDEX = (ROOT / "index.html").read_text()


def run_engine(expression):
    script = f"const e=require('./event-effects.js'); const result=({expression}); process.stdout.write(JSON.stringify(result));"
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def state(*definition_ids, turning_point=2):
    return {"turningPoint": turning_point, "eventState": {"active": [
        {"definitionId": definition_id, "instanceId": f"{definition_id}-1", "startedTurningPoint": turning_point,
         "expiresAfterTurningPoint": turning_point} for definition_id in definition_ids
    ]}}


class TombWorldEventEngineTests(unittest.TestCase):
    def test_every_persistent_event_has_definition_id_handler_and_metadata(self):
        for definition_id in ("dark-of-the-tomb", "my-will-be-done", "countertemporal-shifting", "reanimation-protocols"):
            self.assertIn(f"'{definition_id}':", ENGINE)
            definition = next(line for line in APP.splitlines() if line.strip().startswith(f"'{definition_id}':"))
            for field in ("lifecycle", "duration", "handlerId", "gameplayHooks", "automationType", "priority"):
                self.assertIn(field, definition)
        self.assertNotIn("record.title", ENGINE)
        self.assertNotIn("record.text", ENGINE)

    def test_expired_events_do_not_apply_and_multiple_active_events_do(self):
        expired = state("dark-of-the-tomb"); expired["eventState"]["active"][0]["expiresAfterTurningPoint"] = 1
        self.assertTrue(run_engine(f"e.effectiveAttackRerolls({json.dumps(expired)},{{turningPoint:2,attackerSide:'player',attackType:'shoot',moreThanEight:true}}).attackDice"))
        combined = state("dark-of-the-tomb", "countertemporal-shifting")
        self.assertFalse(run_engine(f"e.effectiveAttackRerolls({json.dumps(combined)},{{turningPoint:2,attackerSide:'player',attackType:'shoot',moreThanEight:true}}).attackDice"))
        self.assertEqual(run_engine(f"e.activeRecords({json.dumps(combined)},2).length"), 2)

    def test_dark_of_tomb_only_disables_long_range_player_shoot_attack_rerolls(self):
        s = json.dumps(state("dark-of-the-tomb"))
        for side, attack, distance, expected in (("player", "shoot", True, False), ("player", "shoot", False, True),
                                                  ("player", "melee", True, True), ("npo", "shoot", True, True)):
            result = run_engine(f"e.effectiveAttackRerolls({s},{{turningPoint:2,attackerSide:'{side}',attackType:'{attack}',moreThanEight:{str(distance).lower()}}})")
            self.assertEqual(result["attackDice"], expected)
            self.assertTrue(result["defenceDice"])

    def test_my_will_be_done_adds_accurate_without_hit_mutation(self):
        s = json.dumps(state("my-will-be-done"))
        result = run_engine(f"e.effectiveWeaponProfile({s},{{hit:4,rules:[]}},{{turningPoint:2,attackerSide:'npo',attackType:'melee',sameRoomAsC1:true}})")
        self.assertEqual(result["hit"], 4)
        self.assertEqual(result["accurate"], 1)
        self.assertIn("Accurate 1", result["rules"])

    def test_countertemporal_is_once_per_qualifying_packet_for_shoot_and_melee(self):
        s = json.dumps(state("countertemporal-shifting"))
        for attack in ("shoot", "melee"):
            packets = run_engine(f"e.resolveCountertemporalPackets({s},[{{damage:2}},{{damage:3}},{{damage:5}}],{{turningPoint:2,attackerSide:'player',defenderSide:'npo',attackType:'{attack}',rollD6:()=>5}})")
            self.assertNotIn("countertemporalRoll", packets[0])
            self.assertEqual([p.get("countertemporalRoll") for p in packets[1:]], [5, 5])
            self.assertEqual([p["finalDamage"] for p in packets], [2, 2, 4])

    def test_countertemporal_ignores_environmental_and_manual_damage(self):
        s = json.dumps(state("countertemporal-shifting"))
        for attack in ("environmental", "manual-correction"):
            packets = run_engine(f"e.resolveCountertemporalPackets({s},[{{damage:5}}],{{turningPoint:2,attackerSide:'environment',defenderSide:'npo',attackType:'{attack}',rollD6:()=>6}})")
            self.assertEqual(packets, [{"damage": 5}])

    def test_event_reanimation_source_and_per_npo_turning_point_limit_are_distinct(self):
        s = json.dumps(state("reanimation-protocols"))
        available = run_engine(f"e.resolveNpoIncapacitation({s},{{turningPoint:2,npoId:'n1',eventAttempts:{{}},candidates:[{{sourceId:'native:reanimation-protocols'}}]}}).candidates")
        self.assertEqual([item["sourceId"] for item in available], ["native:reanimation-protocols", "tomb-world-event:reanimation-protocols"])
        consumed = run_engine(f"e.resolveNpoIncapacitation({s},{{turningPoint:2,npoId:'n1',eventAttempts:{{'2:n1':{{consumed:true}}}},candidates:[]}}).candidates")
        self.assertEqual(consumed, [])
        for marker in ("pending.after=1", "n.ready=false", "discardRemainingAttackDice", "applyTemporaryAplModifier", "aggressive-defence"):
            self.assertIn(marker, APP)

    def test_simultaneous_incapacitation_effects_require_a_persisted_order_choice(self):
        pipeline = APP.split("function applyPendingPlayerDamage", 1)[1].split("function offerReanimateForPendingDamage", 1)[0]
        self.assertIn("showIncapacitationOrderChoice", pipeline)
        self.assertIn("pipelineTransaction.firstSourceId", pipeline)
        self.assertIn("'macrocyte-reanimate'", pipeline)
        self.assertIn("'tomb-world-event:reanimation-protocols'", pipeline)
        self.assertLess(pipeline.index("if(pending.after<=0"), pipeline.index("aggressive-defence:"))

    def test_contextual_messages_are_only_attached_when_an_event_applies(self):
        self.assertIn("combat.eventMessages||combat.profile?.eventMessages", APP)
        self.assertIn("Dark of the Tomb: Attack dice cannot be rerolled", ENGINE)
        self.assertIn("My Will Be Done: This NPO has Accurate 1", ENGINE)
        self.assertIn("Countertemporal Shifting: Resolved one D6", APP)

    def test_subjugation_is_immediate_without_replacement_and_persisted(self):
        definition = next(line for line in APP.splitlines() if line.strip().startswith("'subjugation-glyphs':"))
        self.assertIn("lifecycle:'immediate'", definition)
        self.assertIn("execution:{type:'subjugation-glyphs'}", definition)
        resolution = APP.split("if(type==='subjugation-glyphs')", 1)[1].split("if(type==='living-metal-flux')", 1)[0]
        self.assertIn("remaining.splice(selectedIndex,1)", resolution)
        self.assertIn("transaction.selections", resolution)
        self.assertIn("transaction.rolls", resolution)
        self.assertNotIn("eventState.active.push", resolution)

    def test_transactions_normalize_and_combat_without_events_is_unchanged(self):
        empty = json.dumps(state())
        profile = run_engine(f"e.effectiveWeaponProfile({empty},{{hit:4,rules:['Lethal 5+']}},{{turningPoint:2,attackerSide:'npo',sameRoomAsC1:true}})")
        self.assertEqual(profile, {"hit": 4, "rules": ["Lethal 5+"]})
        packets = run_engine(f"e.resolveCountertemporalPackets({empty},[{{damage:5}}],{{turningPoint:2,attackerSide:'player',defenderSide:'npo',attackType:'shoot'}})")
        self.assertEqual(packets, [{"damage": 5}])
        self.assertIn("transactions:isRecord(importedEvents.transactions)", APP)
        self.assertIn("definitionId=event.definitionId||deckRecord?.definitionId", APP)

    def test_compatibility_surfaces_and_version(self):
        self.assertIn("function normalStrategyEventCount", APP)
        self.assertIn("DeadlyEncounters", APP)
        self.assertIn("const APP_VERSION = '8.6.40';", APP)
        self.assertIn("V8.6.40", INDEX)
        self.assertIn("event-effects.js?v=8.6.40", INDEX)


if __name__ == "__main__":
    unittest.main()
