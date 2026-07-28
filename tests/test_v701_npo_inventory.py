#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class V701NpoInventoryTests(unittest.TestCase):
    def source(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_catalog_is_single_inventory_source_with_21_models(self):
        catalog = self.source("const npoDefinitions = {", "// Official 2D6 table")
        quantities = [int(value) for value in re.findall(r"physicalQuantity:(\d+)", catalog)]
        self.assertEqual(quantities, [3, 10, 2, 1, 3, 1, 1])
        self.assertEqual(sum(quantities), 21)
        self.assertIn("Object.values(npoDefinitions).reduce", APP)
        self.assertEqual(APP.count("const npoDefinitions = {"), 1)

    def test_central_validation_checks_identity_types_limits_and_total(self):
        validation = self.source("function validateNpoRoster", "function commitNpoRoster")
        self.assertIn("Duplicate NPO instance ID", validation)
        self.assertIn("Unsupported NPO type", validation)
        self.assertIn("physicalQuantity", validation)
        self.assertIn("MAX_PHYSICAL_NPOS", validation)
        self.assertIn("Only one Tomb Crawler", validation)
        self.assertIn("unsupported loadout", validation)
        self.assertIn("duplicate display number", validation)

    def test_all_mutating_flows_use_inventory_or_central_validation(self):
        for action in (
            "Generated roster was rejected", "add that NPO", "change that loadout",
            "add a reinforcement", "resolve that event",
        ):
            self.assertIn(action, APP)
        self.assertIn("availableGenerationResult()", self.source("function generateRoster", "function ensureStartingNpoGeneration"))

    def test_generation_uses_active_table_and_stops_cleanly_if_impossible(self):
        generation = self.source("function generateRoster", "function ensureStartingNpoGeneration")
        self.assertIn("state.roster=[]", generation)
        self.assertIn("if(!result)", generation)
        self.assertIn("state.roster=previousRoster", generation)
        self.assertNotRegex(generation, r"Canoptek Macrocyte['\"]")

    def test_manual_selector_uses_only_catalog_and_remaining_inventory(self):
        selector = self.source("function showAddNpo", "function changeNpoLoadout")
        self.assertIn("Object.keys(npoDefinitions)", selector)
        self.assertIn("remaining", selector)
        self.assertIn("disabled", selector)
        self.assertIn("commitNpoRoster", selector)

    def test_supported_instance_loadouts_and_isolator_limit(self):
        catalog = self.source("const npoDefinitions = {", "// Official 2D6 table")
        self.assertIn("twin-gauss-reapers", catalog)
        self.assertIn("transdimensional-isolator", catalog)
        self.assertIn("gauss-scalpel", catalog)
        self.assertIn("tesla-caster", catalog)
        create = self.source("function createNpo", "function rollNpo")
        self.assertIn("weaponId", create)
        self.assertIn("ISOLATOR_LOADOUT", create)

    def test_save_reload_preserves_instance_fields_and_validates_new_saves(self):
        normalized = self.source("function normalizeState", "function npoDefinition")
        npo = self.source("function normalizeNpo", "function mission()")
        self.assertIn("if(Array.isArray(raw.roster))", normalized)
        self.assertLess(normalized.index("validateNpoRoster(raw.roster)"), normalized.index("map(normalizeNpo)"))
        self.assertIn("validateNpoRoster(merged.roster)", normalized)
        self.assertIn("displayNumber", npo)
        self.assertIn("weaponId", npo)

    def test_inventory_counts_each_instance_once_in_every_lifecycle_state(self):
        inventory = self.source("function uniqueNpoInstances", "function validateNpoRoster")
        self.assertIn("seen.has(npo.id)", inventory)
        self.assertNotIn("wounds", inventory)
        self.assertNotIn("battlefieldState", inventory)

    def test_reinforcement_uses_reserves_then_validated_remaining_models(self):
        reinforcement = self.source("function processReinforcementStage", "function reinforcementTriggered")
        picker = self.source("function randomReinforcement", "function nextNpo")
        self.assertIn("reserveNpos().find", reinforcement)
        self.assertIn("commitNpoRoster", reinforcement)
        self.assertIn("npoInventory()[result.type]?.remaining", picker)
        self.assertIn("No legal physical model remains", picker)

    def test_numbering_is_stored_separately_from_unique_id(self):
        create = self.source("function createNpo", "function rollNpo")
        name = self.source("function npoName", "function sortOperativesGlobally")
        self.assertIn("id:uid()", create)
        self.assertIn("displayNumber", create)
        self.assertIn("physicalQuantity<=1", name)
        self.assertIn("n.displayNumber", name)

    def test_deployment_does_not_offer_roster_regeneration(self):
        deployment = self.source("if(stepId==='deploy'){", "const m=mission();")
        self.assertNotIn("Regenerate NPO Roster", deployment)
        self.assertNotIn("regenerateNpoRoster", deployment)
        self.assertNotIn("confirmRegenerateNpoRoster", APP)

    def test_failed_generation_restores_the_previous_roster(self):
        generation = self.source("function generateRoster", "function ensureStartingNpoGeneration")
        self.assertIn("const previousRoster=state.roster", generation)
        self.assertGreaterEqual(generation.count("state.roster=previousRoster"), 2)

    def test_version_and_release_notes_are_701(self):
        self.assertIn("const APP_VERSION = '7.4.2';", APP)
        self.assertIn("V7.4.2", (ROOT / "index.html").read_text())
        self.assertIn("## v7.0.4", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
