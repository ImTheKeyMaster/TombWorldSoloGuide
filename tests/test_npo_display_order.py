#!/usr/bin/env python3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class NpoDisplayOrderTests(unittest.TestCase):
    def source(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_central_helper_uses_visible_names_case_insensitive_natural_order(self):
        helper = self.source("function compareNpoDisplayNames", "function sortOperativesGlobally")
        self.assertIn("npoName(value)", helper)
        self.assertIn("numeric:true", helper)
        self.assertIn("sensitivity:'base'", helper)
        self.assertIn("Array.isArray(npos)?npos:[]", helper)
        self.assertIn("a.index-b.index", helper)

    def test_presentation_sort_does_not_mutate_gameplay_roster(self):
        helper = self.source("function sortedNposForDisplay", "function sortOperativesGlobally")
        global_sort = self.source("function sortOperativesGlobally", "function playerAttackWeapons")
        self.assertIn("[...(Array.isArray(npos)?npos:[])]", helper)
        self.assertNotIn("state.roster.sort", APP)
        self.assertNotIn("state.roster", global_sort)

    def test_roster_setup_deployment_and_tracker_are_sorted_for_display(self):
        setup = self.source("function setupContent", "function bindSetup")
        tracker = self.source("function activationTracker", "function nextStepCard")
        roster = self.source("function renderRoster()", "function renderPlayerRoster()")
        self.assertNotIn("npoRosterCard(npo,false)", setup)
        self.assertIn("sortedNposForDisplay(generation.deployedNpoIds.map", setup)
        self.assertIn("sortedNposForDisplay(state.roster).map(n=>", tracker)
        self.assertIn("sortedNposForDisplay(state.roster).map(n=>npoRosterCard", roster)

    def test_npo_type_and_instance_dropdowns_keep_placeholders_first(self):
        add_npo = self.source("function showAddNpo", "function changeNpoLoadout")
        activation = self.source("function showNpoSelection", "function remainingPlayerOperatives")
        targets = self.source("function showPendingPlayerAttackWizard", "function bindPlayerAttackWizard")
        event = self.source("function strategyEventHtml", "function activationTracker()")
        self.assertIn("types=sortedNposForDisplay(Object.keys(npoDefinitions))", add_npo)
        self.assertIn('Select matching NPO</option>${options}', activation)
        self.assertIn("sortedNposForDisplay(candidates).map", activation)
        self.assertIn('Select a target NPO...</option>${targets.map', targets)
        self.assertIn("targets=sortedNposForDisplay(activeNpos()", targets)
        self.assertIn('Select a Scarab Swarm...</option>${sortedNposForDisplay', event)

    def test_reinforcement_lists_and_controls_share_sorted_copy(self):
        strategy = self.source("function strategyCard", "function strategyEventHtml")
        self.assertIn("deployingNpos=sortedNposForDisplay", strategy)
        self.assertIn("blockedNpos=sortedNposForDisplay", strategy)
        self.assertIn("const placements=deployingNpos.map", strategy)

    def test_event_inline_summary_sorts_after_gameplay_results_are_applied(self):
        event = self.source("function beginCurrentEvent", "function completeCurrentEvent")
        mutation = event.index("npo.wounds=Math.min")
        display_sort = event.index("sortedNposForDisplay(restored.map")
        self.assertLess(mutation, display_sort)
        self.assertIn("restored.push({npo,result:", event)

    def test_gameplay_selection_still_uses_canonical_candidate_order(self):
        activation = self.source("function showNpoSelection", "function remainingPlayerOperatives")
        self.assertIn("const candidates=readyNpos()", activation)
        self.assertIn("candidates[0].id", activation)
        self.assertIn("candidates.find", activation)
        self.assertNotIn("candidates=sortedNposForDisplay", activation)

    def test_instance_identity_and_save_reload_paths_are_not_changed_by_sorting(self):
        create = self.source("function createNpo", "function rollNpo")
        normalize = self.source("function normalizeState", "function npoDefinition")
        self.assertIn("id:uid()", create)
        self.assertIn("displayNumber", create)
        self.assertIn("map(normalizeNpo)", normalize)
        self.assertNotIn("sortedNposForDisplay", normalize)


if __name__ == "__main__":
    unittest.main()
