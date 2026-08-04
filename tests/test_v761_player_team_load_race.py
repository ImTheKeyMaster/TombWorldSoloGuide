import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


class PlayerTeamLoadRaceTests(unittest.TestCase):
    def test_01_no_team_cannot_build(self): self.assertIn("state.playerTeamId&&playerTeamLoadStatus==='loaded'", APP)
    def test_02_selection_is_synchronous(self): self.assertIn("state.playerTeamId=teamId;", APP)
    def test_03_selection_invalidates_loaded_identity(self): self.assertIn("loadedPlayerTeamId=null;", APP)
    def test_04_loading_button_text(self): self.assertIn("Loading Team...", APP)
    def test_05_loaded_status_required(self): self.assertIn("playerTeamLoadStatus==='loaded'", APP)
    def test_06_loaded_identity_must_match(self): self.assertIn("loadedPlayerTeamId===state.playerTeamId", APP)
    def test_07_stale_success_is_ignored(self): self.assertGreaterEqual(APP.count("requestId!==playerTeamLoadRequestId||state.playerTeamId!==teamId"), 2)
    def test_08_stale_failure_is_ignored(self): self._run_stale_failure_harness()
    def test_09_out_of_order_success_keeps_newest_team(self): self._run_race_harness("success")
    def test_10_newer_team_finishing_first_remains_loaded(self): self._run_race_harness("success")
    def test_11_disabled_button_blocks_clicks(self): self.assertIn("disabled aria-disabled=", APP)
    def test_12_navigation_handler_has_guard(self): self.assertIn("if(stepId==='team'&&!canBuildPlayerRoster())", APP)
    def test_13_rapid_navigation_is_locked(self):
        self.assertIn("if(setupNavigationInProgress)return;", APP)
        self.assertIn("if(currentSetupStepId()!==stepId)return;", APP)
    def test_14_roster_render_is_guarded(self): self.assertIn("if(!canBuildPlayerRoster())", APP[APP.index("function renderSetup"):])
    def test_15_old_team_data_is_cleared_on_selection(self): self.assertIn("playerTeamData=null;", APP[APP.index("function selectPlayerTeam"):])
    def test_16_changing_team_clears_roster(self): self.assertIn("clearPlayerTeamDependentState();", APP[APP.index("function selectPlayerTeam"):])
    def test_17_same_team_selection_retries(self): self.assertNotIn("if(state.playerTeamId!==button.dataset.playerTeam)", APP)
    def test_18_failure_disables_and_reports(self):
        self.assertIn("playerTeamLoadStatus='error';", APP)
        self.assertIn('role="alert"', APP)
    def test_19_restored_selection_is_reloaded(self): self.assertIn("await loadPlayerTeamData(state.playerTeamId);", APP)
    def test_20_restored_roster_waits_for_matching_data(self): self.assertIn("Loading the selected Kill Team before displaying its operatives.", APP)
    def test_21_stale_roster_ids_are_cleared(self): self.assertIn("some(id=>!operativeIds.has(id))", APP)
    def test_22_roster_rules_remain_present(self):
        for rule in ("maxGunners", "maxGravis", "selectionGroupMax", "mandatoryTroopers"):
            self.assertIn(rule, APP)
    def test_23_numbering_remains_present(self): self.assertIn("assignPlayerDisplayNumbers();", APP)
    def test_24_current_version_is_763(self):
        self.assertIn("const APP_VERSION = '8.6.37';", APP)
        self.assertIn("const APP_VERSION = '8.6.37';", WORKER)
        self.assertIn("V8.6.37", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.37"))
    def test_25_loading_and_error_are_accessible(self):
        self.assertIn('role="status"', APP)
        self.assertIn('role="alert"', APP)

    def _run_race_harness(self, _mode):
        start = APP.index("  let playerManifest=null;")
        end = APP.index("  function validatePlayerTeamData")
        source = APP[start:end]
        script = f"""
const assert=require('assert');
let state={{playerTeamId:'',playerRoster:[],playerDisplayNumbers:{{}}}};
let pending={{}};
const fetch=path=>new Promise((resolve,reject)=>pending[path]={{resolve,reject}});
const render=()=>{{}}; const save=()=>true; const assignPlayerDisplayNumbers=()=>{{}};
const clearPlayerTeamDependentState=()=>{{state.playerRoster=[];}};
const validatePlayerTeamData=(data)=>{{if(!data.operatives)throw Error('invalid');}};
{source}
playerManifest={{teams:[{{id:'a',file:'a.json'}},{{id:'b',file:'b.json'}}]}};
state.playerTeamId='a'; const a=loadPlayerTeamData('a');
state.playerTeamId='b'; const b=loadPlayerTeamData('b');
pending['Player_Operatives/b.json'].resolve({{ok:true,json:async()=>({{teamId:'b',operatives:[{{id:'b1'}}]}})}});
(async()=>{{await b; assert.equal(loadedPlayerTeamId,'b'); assert.equal(playerTeamData.teamId,'b');
pending['Player_Operatives/a.json'].resolve({{ok:true,json:async()=>({{teamId:'a',operatives:[{{id:'a1'}}]}})}});
await a; assert.equal(loadedPlayerTeamId,'b'); assert.equal(playerTeamData.teamId,'b');}})().catch(e=>{{console.error(e);process.exit(1);}});
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)

    def _run_stale_failure_harness(self):
        start = APP.index("  let playerManifest=null;")
        end = APP.index("  function validatePlayerTeamData")
        source = APP[start:end]
        script = f"""
const assert=require('assert');
let state={{playerTeamId:'',playerRoster:[],playerDisplayNumbers:{{}}}};
let pending={{}}; let renders=0;
const fetch=path=>new Promise((resolve,reject)=>pending[path]={{resolve,reject}});
const render=()=>{{renders++;}}; const save=()=>true; const assignPlayerDisplayNumbers=()=>{{}};
const clearPlayerTeamDependentState=()=>{{state.playerRoster=[];}};
const validatePlayerTeamData=(data)=>{{if(!data.operatives)throw Error('invalid');}};
{source}
playerManifest={{teams:[{{id:'a',file:'a.json'}},{{id:'b',file:'b.json'}}]}};
state.playerTeamId='a'; const a=loadPlayerTeamData('a');
state.playerTeamId='b'; const b=loadPlayerTeamData('b');
pending['Player_Operatives/a.json'].reject(Error('Team A failed'));
(async()=>{{await a; assert.equal(playerTeamLoadStatus,'loading'); assert.equal(playerTeamLoadError,null);
pending['Player_Operatives/b.json'].resolve({{ok:true,json:async()=>({{teamId:'b',operatives:[{{id:'b1'}}]}})}});
await b; assert.equal(playerTeamLoadStatus,'loaded'); assert.equal(loadedPlayerTeamId,'b'); assert.equal(playerTeamLoadError,null);}})().catch(e=>{{console.error(e);process.exit(1);}});
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
