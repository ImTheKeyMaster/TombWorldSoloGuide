import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class PlayerTargetWoundLabelsTests(unittest.TestCase):
    def test_release_version_is_consistent(self):
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.60"))
        self.assertIn("Version 8.6.5 - Show Player Wounds in Target Selection", README)
        self.assertIn("const APP_VERSION = '8.6.60';", APP)
        self.assertIn("const APP_VERSION = '8.6.60';", WORKER)
        self.assertIn("V8.6.60", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.60", INDEX)

    def test_shared_helper_uses_numbered_name_and_live_wounds(self):
        helper = re.search(r"function playerTargetLabel\(id\)\{(.*?)\n  \}", APP, re.S)
        self.assertIsNotNone(helper)
        body = helper.group(1)
        self.assertIn("playerName(id)", body)
        self.assertIn("playerCurrentWounds(id)", body)
        self.assertIn("playerDefinition(id)?.wounds", body)
        self.assertIn("Number.isFinite(maximum)&&maximum>0", body)
        self.assertIn("${name} (${current}/${maximum} wounds)", body)
        self.assertIn("${name} (${current} wounds)", body)

    def test_helper_formats_normal_and_missing_maximum_values(self):
        script = r"""
const state={playerWounds:{bombard:9,unknown:4}};
const definitions={bombard:{name:'Bombard',wounds:15},unknown:{name:'Unknown'}};
function playerDefinition(id){return definitions[id]||null;}
function playerCurrentWounds(id){return state.playerWounds[id];}
function playerName(id){return definitions[id]?.name||id;}
function playerTargetLabel(id){
  const name=playerName(id);
  const current=Math.max(0,Number(playerCurrentWounds(id)||0));
  const maximum=Number(playerDefinition(id)?.wounds);
  return Number.isFinite(maximum)&&maximum>0
    ? `${name} (${current}/${maximum} wounds)`
    : `${name} (${current} wounds)`;
}
if(playerTargetLabel('bombard')!=='Bombard (9/15 wounds)')process.exit(1);
if(playerTargetLabel('unknown')!=='Unknown (4 wounds)')process.exit(2);
state.playerWounds.bombard=3;
if(playerTargetLabel('bombard')!=='Bombard (3/15 wounds)')process.exit(3);
state.playerWounds.bombard=12;
if(playerTargetLabel('bombard')!=='Bombard (12/15 wounds)')process.exit(4);
"""
        subprocess.run(["node", "-e", script], check=True, cwd=ROOT)

    def test_npo_shoot_and_fight_options_keep_ids_order_and_manual_choice(self):
        renderer = re.search(r"function renderNpoDecisionResult\(.*?\n  \}", APP, re.S).group(0)
        self.assertIn("eligibleTargetIds.map(id=>`<option value=", renderer)
        self.assertIn("playerTargetLabel(id)", renderer)
        self.assertNotIn("eligibleTargetIds.sort", renderer)
        self.assertNotIn("playerCurrentWounds(a)", renderer)
        self.assertIn("if(!targetConfirmed&&eligibleTargetIds.length===1)", renderer)
        self.assertIn("<select id=\"npoPriorityTarget\"", renderer)
        self.assertRegex(renderer, r"decision\.action\.includes\('Fight'\).*decision\.action\.includes\('Shoot'\)")

    def test_confirmed_and_single_target_fields_show_wounds(self):
        self.assertIn("const targetName=state.npoAttackTargetId?playerTargetLabel(state.npoAttackTargetId):'';", APP)
        self.assertIn("targetConfirmed||eligibleTargetIds.length===1", APP)
        self.assertIn("value=\"${escapeHtml(targetName)}\" readonly", APP)

    def test_special_action_player_selectors_show_wounds(self):
        self.assertIn("remainingPlayerOperatives().map(id=>`<option value=\"${escapeHtml(id)}\">${escapeHtml(playerTargetLabel(id))}</option>`)", APP)
        self.assertIn("'cranial-overload'", APP)

    def test_geomantic_player_checkboxes_show_wounds_and_accessible_labels(self):
        self.assertIn("label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id)", APP)
        self.assertIn("data-disturbance-target", APP)
        self.assertIn("aria-label=\"${escapeHtml(target.ariaLabel)}\"", APP)
        self.assertIn("Select ${name}, ${current} of ${maximum} wounds", APP)

    def test_blast_and_torrent_player_targets_show_current_wounds(self):
        player_attack_targets = "label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id),wounds:playerCurrentWounds(id)"
        self.assertGreaterEqual(APP.count(player_attack_targets), 2)
        self.assertIn("ruleId==='blast'?[...playerTargets,...npoTargets]:playerTargets", APP)
        self.assertIn("eligible.map(weaponRuleTargetOption)", APP)
        self.assertIn("value=\"${id}\" data-weapon-rule-target", APP)

    def test_target_labels_are_recomputed_when_each_screen_renders(self):
        self.assertIn("eligibleTargetIds.map(id=>", APP)
        self.assertIn("playerTargetLabel(id)", APP)
        self.assertNotIn("playerTargetLabel:", PERSISTENCE)
        self.assertNotIn("targetLabel:", PERSISTENCE)

    def test_eligibility_and_duplicate_numbering_remain_in_use(self):
        self.assertIn("const eligibleTargetIds=eligibleNpoAttackTargets();", APP)
        self.assertIn("state.npoAttackTargetId&&!eligibleTargetIds.includes(state.npoAttackTargetId)", APP)
        self.assertIn("state.npoAttackTargetId=null;", APP)
        self.assertIn("inPlayLivingPlayerOperativeIds().map", APP)
        self.assertIn("const name=playerName(id);", APP)

    def test_random_relocation_reporting_remains_name_only(self):
        self.assertIn("transaction.selections.map((id,index)=>`${playerName(id)} rolled ${transaction.rolls[index]}`)", APP)
        self.assertNotIn("transaction.selections.map((id,index)=>`${playerTargetLabel(id)}", APP)

    def test_save_schema_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
        self.assertNotIn("playerTargetLabel", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
