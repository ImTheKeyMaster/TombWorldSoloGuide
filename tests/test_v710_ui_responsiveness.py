import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


class V710UiResponsivenessTests(unittest.TestCase):
    def source(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_mission_selection_renders_before_dependent_load(self):
        binding = self.source("function bindSetup", "function runStartingNpoGeneration")
        handler = binding.split("$$('.mission-choice')", 1)[1].split("$('#setupHome')", 1)[0]
        self.assertLess(handler.index("state.missionId=missionId"), handler.index("render()"))
        self.assertLess(handler.index("render()"), handler.index("setTimeout"))
        self.assertLess(handler.index("setTimeout"), handler.index("loadObjectiveMission(missionId)"))
        self.assertNotIn("onclick=async", handler)
        self.assertIn('aria-pressed="${state.missionId===m.id}"', APP)
        self.assertIn("state.missionId===m.id?'selected':''", APP)
        self.assertNotIn("state.screen='game'", handler)

    def test_latest_mission_load_wins_and_failure_preserves_selection(self):
        loader = self.source("async function loadObjectiveMission", "let playerManifest")
        self.assertIn("const requestId=++missionLoadRequestId", loader)
        self.assertGreaterEqual(loader.count("requestId!==missionLoadRequestId||state.missionId!==missionId"), 3)
        self.assertLess(loader.index("await TombWorldMissionEngine.loadMissionDefinition"), loader.index("objectiveDefinition=definition"))
        stale_guard = loader.index("requestId!==missionLoadRequestId||state.missionId!==missionId")
        self.assertLess(stale_guard, loader.index("objectiveDefinition=definition"))
        self.assertIn("showToast('Mission automation could not be loaded.", loader)
        self.assertIn("objectiveEngine=null;objectiveDefinition=null", loader.split("catch(error)", 1)[1])
        self.assertNotIn("state.missionId=", loader)

    def test_deployment_has_no_editor_or_regeneration_control(self):
        deployment = self.source("if(stepId==='deploy'){", "const m=mission();")
        binding = self.source("function bindSetup", "function runStartingNpoGeneration")
        self.assertNotIn("Edit generated NPO roster", deployment)
        self.assertNotIn("addSetupNpo", deployment)
        self.assertNotIn("regenerateNpoRoster", deployment)
        self.assertNotIn("Regenerate NPO Roster", deployment)
        self.assertNotIn("confirmRegenerateNpoRoster", binding)
        self.assertIn("generation.deployedNpoIds", deployment)
        self.assertIn('id="npoDeployed"', deployment)
        self.assertIn('id="playerDeployed"', deployment)

    def test_deployed_npo_delimiters_are_joined_between_sorted_names(self):
        deployment = self.source("if(stepId==='deploy'){", "const m=mission();")
        self.assertIn("sortedNposForDisplay(generation.deployedNpoIds.map", deployment)
        self.assertIn(".filter(Boolean)).map(npo=>escapeHtml(npoName(npo))))", deployment)
        self.assertIn('class="deployment-roster">${deployedNpoRoster}</span>', deployment)
        self.assertNotIn('class="deployment-roster">• ${deployedNpoRoster}', deployment)

    def test_npo_profile_precedes_bottom_action_area(self):
        card = self.source("function npoRosterCard", "function operativeCard")
        self.assertLess(card.index("npoProfileDetailsHtml(n,definition)"), card.index('class="npo-card-actions"'))
        self.assertLess(card.index('class="wound-controls"'), card.index('class="quick-actions"'))
        self.assertLess(card.index("+ Heal"), card.index("Remove NPO"))
        self.assertIn(".npo-card-actions{margin-top:auto;padding-top:14px}", CSS)
        self.assertIn(".npo-card-actions .wound-controls{margin-top:0}", CSS)
        self.assertIn(".npo-roster-card{position:relative;display:flex;flex-direction:column", CSS)
        self.assertIn("− Wound", card)
        self.assertIn("+ Heal", card)
        self.assertIn("npo-roster-card.dead", CSS)

    def test_release_version_is_synchronized(self):
        self.assertIn("const APP_VERSION = '8.6.58';", APP)
        self.assertIn("const APP_VERSION = '8.6.58';", WORKER)
        self.assertIn("V8.6.58", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.58", INDEX)


if __name__ == "__main__":
    unittest.main()
