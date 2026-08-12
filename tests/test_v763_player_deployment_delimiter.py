import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
SETUP = APP[APP.index("  function setupContent(stepId)"):
            APP.index("  function bindSetup(stepId)")]
DEPLOYMENT = SETUP[SETUP.index("    if(stepId==='deploy')"):]


class PlayerDeploymentDelimiterTests(unittest.TestCase):
    def test_01_player_deployment_has_no_leading_bullet_or_dot(self):
        self.assertIn(
            "const playerRoster=inlineOperativeList((state.playerRoster||[]).map(id=>escapeHtml(playerName(id))))",
            DEPLOYMENT,
        )
        self.assertNotIn('class="deployment-roster">• ${playerRoster}', DEPLOYMENT)
        self.assertNotIn('class="deployment-roster">· ${playerRoster}', DEPLOYMENT)

    def test_02_inline_list_has_exactly_one_separator_between_names(self):
        helper = APP[APP.index("function inlineOperativeList"):
                     APP.index("\n", APP.index("function inlineOperativeList"))]
        self.assertIn("names.filter(Boolean).join(' · ')", helper)
        script = f"""
{helper}
const assert=require('assert');
assert.equal(inlineOperativeList(['Scout Heavy Gunner','Scout Hunter','Scout Sergeant']),
  'Scout Heavy Gunner · Scout Hunter · Scout Sergeant');
assert.equal(inlineOperativeList(['Scout Hunter']),'Scout Hunter');
assert.equal(inlineOperativeList([]),'');
assert.equal(inlineOperativeList(['','Scout Hunter',null]),'Scout Hunter');
assert.equal(inlineOperativeList([
  'Scout Heavy Gunner (Missile Launcher)','Scout Hunter',
  'Scout Sergeant (Bolt Pistol & Chainsword)','Scout Tracker',
  'Scout Warrior 1 (Astartes Shotgun)','Scout Warrior 2 (Bolt Pistol & Combat Blade)',
  'Scout Warrior 3 (Astartes Shotgun)','Scout Warrior 4 (Astartes Shotgun)',
  'Scout Warrior 5 (Astartes Shotgun)'
]),'Scout Heavy Gunner (Missile Launcher) · Scout Hunter · Scout Sergeant (Bolt Pistol & Chainsword) · Scout Tracker · Scout Warrior 1 (Astartes Shotgun) · Scout Warrior 2 (Bolt Pistol & Combat Blade) · Scout Warrior 3 (Astartes Shotgun) · Scout Warrior 4 (Astartes Shotgun) · Scout Warrior 5 (Astartes Shotgun)');
"""
        subprocess.run(["node", "-e", script], check=True)

    def test_03_player_roster_preserves_numbering_variants_and_order(self):
        self.assertIn(
            "(state.playerRoster||[]).map(id=>escapeHtml(playerName(id)))",
            DEPLOYMENT,
        )
        self.assertNotIn(".sort(", DEPLOYMENT[DEPLOYMENT.index("const playerRoster="):
                                              DEPLOYMENT.index("const deploymentDetails=")])
        self.assertIn("function playerDisplayIdentity(id)", APP)
        self.assertIn("const storedNumber=state.playerDisplayNumbers?.[id]", APP)
        self.assertIn("suffix:match?.[2]||''", APP)

    def test_04_npo_deployment_still_has_no_leading_delimiter_and_keeps_sorting(self):
        self.assertIn(
            "const deployedNpoRoster=inlineOperativeList(sortedNposForDisplay(",
            DEPLOYMENT,
        )
        self.assertIn(
            'class="deployment-roster">${deployedNpoRoster}</span>',
            DEPLOYMENT,
        )
        self.assertNotIn('class="deployment-roster">• ${deployedNpoRoster}', DEPLOYMENT)
        self.assertNotIn('class="deployment-roster">· ${deployedNpoRoster}', DEPLOYMENT)

    def test_05_selected_roster_summary_has_no_leading_delimiter(self):
        summary = SETUP[SETUP.index("<strong>Selected roster</strong>"):
                        SETUP.index("    if(stepId==='deploy')")]
        self.assertIn(
            "inlineOperativeList(selectedDefs.map(o=>escapeHtml(playerName(o.id))))",
            summary,
        )
        self.assertNotIn("<br>•", summary)
        self.assertNotIn("<br>·", summary)

    def test_06_no_prefixed_or_empty_deployment_roster_markup(self):
        self.assertNotIn('<span class="deployment-roster">•', APP)
        self.assertNotIn('<span class="deployment-roster">·', APP)
        self.assertIn(
            "const playerRosterHtml=playerRoster?`<span class=\"deployment-roster\">${playerRoster}</span>`:''",
            DEPLOYMENT,
        )

    def test_07_deployment_checkbox_behavior_is_unchanged(self):
        self.assertIn('id="playerDeployed" type="checkbox"', DEPLOYMENT)
        self.assertIn("state.playerDeployed?'checked':''", DEPLOYMENT)
        self.assertIn("playerValid?'':'disabled'", DEPLOYMENT)
        self.assertIn("$('#playerDeployed')?.addEventListener('change'", APP)
        self.assertIn("$('#checkAllDeployment')?.addEventListener('click'", APP)

    def test_08_application_displays_version_763(self):
        self.assertIn("const APP_VERSION = '8.6.55';", APP)
        self.assertIn("const APP_VERSION = '8.6.55';", WORKER)
        self.assertIn("V8.6.55", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.55"))
        self.assertIn("## v8.6.25", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js",
                      "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.55", INDEX)


if __name__ == "__main__":
    unittest.main()
