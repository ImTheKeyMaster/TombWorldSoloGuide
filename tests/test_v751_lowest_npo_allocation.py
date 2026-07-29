#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


class LowestNpoAllocationTests(unittest.TestCase):
    def allocate(self, quantity, allocated=(), definition=None):
        helper = "function lowestAvailableNpoInstances" + source(
            "function lowestAvailableNpoInstances", "function validateNpoRoster"
        )
        definition = definition or {"id": "necron-warrior", "type": "Necron Warrior", "physicalQuantity": 10}
        roster = [
            {"id": f"legacy-{number}", "type": definition["type"], "displayNumber": number}
            for number in allocated
        ]
        script = f"""
const state={{roster:{json.dumps(roster)}}};
const definition={json.dumps(definition)};
function npoDefinition(type){{return type===definition.type?definition:null;}}
function isRecord(value){{return value&&typeof value==='object'&&!Array.isArray(value);}}
function uniqueNpoInstances(roster=state.roster){{
  const seen=new Set();
  return roster.filter(npo=>isRecord(npo)&&typeof npo.id==='string'&&npo.id&&!seen.has(npo.id)&&seen.add(npo.id));
}}
{helper}
process.stdout.write(JSON.stringify(lowestAvailableNpoInstances(definition.type,{quantity})));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        return json.loads(result.stdout)

    def test_unused_inventory_returns_one_and_two_deterministically(self):
        first = self.allocate(2)
        self.assertEqual([item["displayNumber"] for item in first], [1, 2])
        self.assertEqual(first, self.allocate(2))
        self.assertEqual([item["id"] for item in first], ["necron-warrior-1", "necron-warrior-2"])

    def test_allocated_numbers_are_skipped_without_renumbering(self):
        self.assertEqual([item["displayNumber"] for item in self.allocate(2, (1, 2))], [3, 4])
        self.assertEqual([item["displayNumber"] for item in self.allocate(2, (1, 3))], [2, 4])

    def test_ten_warriors_use_natural_numeric_order_and_inventory_limit(self):
        allocated = self.allocate(11)
        self.assertEqual([item["displayNumber"] for item in allocated], list(range(1, 11)))
        self.assertGreater(allocated.index(next(item for item in allocated if item["displayNumber"] == 10)),
                           allocated.index(next(item for item in allocated if item["displayNumber"] == 9)))

    def test_single_model_type_is_unavailable_even_for_legacy_instance_ids(self):
        geomancer = {"id": "geomancer", "type": "Geomancer", "physicalQuantity": 1}
        self.assertEqual(self.allocate(1, definition=geomancer), [{"id": "geomancer-1", "displayNumber": None}])
        self.assertEqual(self.allocate(1, (1,), geomancer), [])

    def test_every_creation_path_uses_the_central_allocator(self):
        create = source("function createNpo", "function rollNpo")
        self.assertIn("lowestAvailableNpoInstances(type,1", create)
        for call in ("generateRoster", "processReinforcementStage", "resolveStrategyEvent", "showAddNpo"):
            self.assertIn("createNpo(", source(f"function {call}", "\n  function "))
        self.assertIn("createNpo(", source("function createCeaselessScuttlingWarrior", "function aggressiveDefenceDamage"))

    def test_starting_selection_keeps_random_types_but_uses_lowest_instances(self):
        selection = source("function selectStartingNpos", "function generateRoster")
        self.assertIn("selectedTypeCounts", selection)
        self.assertIn("Number(a.displayNumber)", selection)
        self.assertIn("slice(0,quantity)", selection)
        self.assertIn("Math.random()", selection)

    def test_events_reinforcements_and_loadout_limits_are_preserved(self):
        self.assertIn("event.execution.type==='chittering-drone'", APP)
        self.assertIn("event.execution.type==='awakened-warrior'", APP)
        self.assertIn("reserveNpos().find", source("function processReinforcementStage", "function reinforcementTriggered"))
        validation = source("function validateNpoRoster", "function commitNpoRoster")
        self.assertIn("Only one Tomb Crawler", validation)
        self.assertIn("physicalQuantity", validation)

    def test_existing_saves_keep_valid_numbers_and_setup_deletion_does_not_renumber(self):
        normalization = source("function normalizeState", "function npoDefinition")
        self.assertIn("Number.isInteger(npo.displayNumber)", normalization)
        deletion = source("function deleteNpo", "function animateMissionDice")
        self.assertNotIn("displayNumber=", deletion)

    def test_activation_and_event_order_code_is_unchanged_by_allocation(self):
        helper = source("function lowestAvailableNpoInstances", "function validateNpoRoster")
        self.assertNotIn("activation", helper.lower())
        self.assertNotIn("eventState", helper)
        self.assertNotIn("Math.random", helper)

    def test_reported_starting_roster_displays_exact_lowest_number_example(self):
        display_functions = "function operativeName" + source("function operativeName", "function allocateDisplayNumber")
        display_functions += "function npoName" + source("function npoName", "function sortOperativesGlobally")
        roster = [
            {"id": "scarab-2", "type": "Canoptek Scarab Swarm", "displayNumber": 2},
            {"id": "warrior-2", "type": "Necron Warrior", "displayNumber": 2},
            {"id": "crawler-1", "type": "Canoptek Tomb Crawler", "displayNumber": 1},
            {"id": "scarab-1", "type": "Canoptek Scarab Swarm", "displayNumber": 1},
            {"id": "warrior-1", "type": "Necron Warrior", "displayNumber": 1},
        ]
        script = f"""
const definitions={{
  'Canoptek Scarab Swarm':{{physicalQuantity:3}},
  'Canoptek Tomb Crawler':{{physicalQuantity:2}},
  'Necron Warrior':{{physicalQuantity:10}}
}};
function npoDefinition(type){{return definitions[type]||null;}}
function playerDefinition(){{return null;}}
const state={{roster:{json.dumps(roster)},playerRoster:[]}};
{display_functions}
process.stdout.write(sortedNposForDisplay({json.dumps(roster)}).map(npoName).join(' · '));
"""
        displayed = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True).stdout
        self.assertEqual(
            displayed,
            "Canoptek Scarab Swarm 1 · Canoptek Scarab Swarm 2 · Canoptek Tomb Crawler · Necron Warrior 1 · Necron Warrior 2",
        )


if __name__ == "__main__":
    unittest.main()
