import unittest
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class PlayerOperativeNumberingTests(unittest.TestCase):
    def test_finalized_numbers_are_persisted_by_operative_id(self):
        self.assertIn("playerDisplayNumbers:{}", APP)
        self.assertIn("if(stepId==='playerRoster')assignPlayerDisplayNumbers()", APP)
        self.assertIn("state.playerDisplayNumbers[id]=allocateDisplayNumber(used)", APP)
        self.assertIn("merged.playerDisplayNumbers=isRecord(raw?.playerDisplayNumbers)", APP)

    def test_player_and_npo_numbering_share_the_same_allocator(self):
        self.assertIn("function allocateDisplayNumber(usedNumbers,preferredNumber)", APP)
        self.assertIn("npo.displayNumber=allocateDisplayNumber(used,preferredNumber)", APP)
        self.assertIn("state.playerDisplayNumbers[id]=allocateDisplayNumber(used)", APP)

    def test_display_name_uses_current_roster_without_renumbering_casualties(self):
        operative_name = APP[APP.index("function operativeName"):APP.index("function allocateDisplayNumber")]
        self.assertIn("state.playerRoster||[]", operative_name)
        self.assertIn("state.roster||[]", operative_name)
        self.assertNotIn("playerCasualtyIds", operative_name)
        self.assertNotIn("livingPlayerOperative", operative_name)

    def test_player_and_npo_names_use_one_shared_formatter(self):
        self.assertIn("return operativeName(id,'player')", APP)
        self.assertIn("return operativeName(n,'npo')", APP)

    def test_source_instance_numbers_are_replaced_after_selection(self):
        self.assertIn("function playerDisplayIdentity(id)", APP)
        self.assertIn("definition?.officialName?sourceName.match(/^(.*?)\\s+\\d+(\\s*\\(.*\\))?$/):null", APP)
        self.assertIn("const storedNumber=state.playerDisplayNumbers?.[id]", APP)
        self.assertIn("playerDisplayIdentity(item).groupName===identity.groupName", APP)

    def test_saved_display_numbers_are_canonicalized_after_team_data_loads(self):
        load_team = APP[APP.index("async function loadPlayerTeamData"):APP.index("function validatePlayerTeamData")]
        self.assertIn("assignPlayerDisplayNumbers()", load_team)

    def test_mixed_source_numbers_and_loadouts_receive_sequential_names(self):
        helpers = APP[APP.index("function playerDisplayIdentity"):APP.index("let missions=[]")]
        script = f"""
const assert=require('assert');
const playerTeamData={{operatives:[
  {{id:'trooper-2-rifle',name:'Trooper 2 (Lasrifle)',officialName:'Spectre Trooper'}},
  {{id:'trooper-3-carbine',name:'Trooper 3 (Lascarbine)',officialName:'Spectre Trooper'}},
  {{id:'trooper-6-rifle',name:'Trooper 6 (Lasrifle)',officialName:'Spectre Trooper'}},
  {{id:'trooper-7-carbine',name:'Trooper 7 (Lascarbine)',officialName:'Spectre Trooper'}},
  {{id:'trooper-8-rifle',name:'Trooper 8 (Lasrifle)',officialName:'Spectre Trooper'}},
  {{id:'trooper-9-carbine',name:'Trooper 9 (Lascarbine)',officialName:'Spectre Trooper'}}
]}};
const state={{playerRoster:playerTeamData.operatives.map(item=>item.id),playerDisplayNumbers:{{
  'trooper-2-rifle':2,'trooper-3-carbine':3,'trooper-6-rifle':6,
  'trooper-7-carbine':7,'trooper-8-rifle':8,'trooper-9-carbine':9
}},roster:[]}};
function playerDefinition(id){{return playerTeamData.operatives.find(item=>item.id===id)||null;}}
function npoDefinition(){{return null;}}
{helpers}
assignPlayerDisplayNumbers();
assert.deepEqual(state.playerRoster.map(playerName),[
  'Trooper 1 (Lasrifle)','Trooper 2 (Lascarbine)','Trooper 3 (Lasrifle)',
  'Trooper 4 (Lascarbine)','Trooper 5 (Lasrifle)','Trooper 6 (Lascarbine)'
]);
assert.deepEqual(state.playerRoster,playerTeamData.operatives.map(item=>item.id));
playerTeamData.operatives.push({{id:'agent-47',name:'Agent 47'}});
state.playerRoster=['agent-47'];
assignPlayerDisplayNumbers();
assert.equal(playerName('agent-47'),'Agent 47');
"""
        subprocess.run(["node", "-e", script], check=True)

    def test_special_action_messages_do_not_bypass_the_shared_formatter(self):
        self.assertNotIn("target.name||npoName(target)", APP)
        self.assertIn("action.target?.side==='enemy'?playerName(targetId):npoName(target)", APP)

    def test_roster_and_auxiliary_views_use_canonical_player_name(self):
        for expected in (
            "chosen?playerName(o.id):o.name",
            "selectedDefs.map(o=>escapeHtml(playerName(o.id)))",
            "map(id=>escapeHtml(playerName(id)))",
            "<h4>${escapeHtml(playerName(id))}</h4>",
            "label:`Player — ${playerName(operative.id)}`",
        ):
            self.assertIn(expected, APP)


if __name__ == "__main__":
    unittest.main()
