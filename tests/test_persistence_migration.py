import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PersistenceMigrationTests(unittest.TestCase):
    def test_save_schema_migration_validation_and_idempotency(self):
        script = r"""
const assert=require('assert');
const persistence=require('./persistence.js');
const {currentSaveVersion,migrateSave,createPersistedSave,migrations}=persistence;

assert.equal(currentSaveVersion(),1);
assert.equal(typeof migrations[0],'function');

const unversioned=migrateSave({missionId:'04',roster:[],playerRoster:[]});
assert.equal(unversioned.saveVersion,1);
assert.deepEqual(unversioned.missionState,{});
assert.deepEqual(unversioned.reinforcementState,{operativeIds:[],blockedOperativeIds:[]});

const versionZero=migrateSave({saveVersion:0,roster:[],playerRoster:[]});
assert.equal(versionZero.saveVersion,1);

const latest=migrateSave({saveVersion:1,roster:[],playerRoster:[],missionState:{destruction:4}});
assert.equal(latest.missionState.destruction,4);

const corrupted=migrateSave({
  saveVersion:0,turningPoint:'bad',threat:null,roster:'bad',playerRoster:{},journal:'bad',
  missionState:null,missionRuntime:[],strategyData:'bad',eventState:[],reinforcementState:null
});
assert.equal(corrupted.turningPoint,0);
assert.equal(corrupted.threat,0);
assert.deepEqual(corrupted.roster,[]);
assert.deepEqual(corrupted.playerRoster,[]);
assert.deepEqual(corrupted.missionState,{});
assert.equal(corrupted.missionRuntime,null);
assert.equal(corrupted.strategyData,null);
assert.deepEqual(corrupted.eventState,{});
assert.deepEqual(corrupted.reinforcementState,{operativeIds:[],blockedOperativeIds:[]});

const references=migrateSave({
  saveVersion:1,
  roster:[{id:'valid'},null,{bad:true}],playerRoster:['marine'],
  newIds:['valid','missing'],playerActivatedIds:['marine','missing'],playerCasualtyIds:['missing'],
  reinforcementState:{operativeIds:['valid','missing'],blockedOperativeIds:['valid','missing']}
});
assert.deepEqual(references.newIds,['valid']);
assert.deepEqual(references.playerActivatedIds,['marine']);
assert.deepEqual(references.playerCasualtyIds,[]);
assert.deepEqual(references.playerOperativeStates,{marine:{inPlay:true}});

const offBoard=migrateSave({saveVersion:1,roster:[],playerRoster:['marine'],playerOperativeStates:{marine:{inPlay:false,offBoardReason:'escaped'}}});
assert.deepEqual(offBoard.playerOperativeStates,{marine:{inPlay:false,offBoardReason:'escaped'}});
assert.deepEqual(createPersistedSave(offBoard).playerOperativeStates,offBoard.playerOperativeStates);
assert.deepEqual(references.reinforcementState.operativeIds,['valid']);
assert.deepEqual(references.reinforcementState.blockedOperativeIds,[]);

assert.throws(
  ()=>migrateSave({saveVersion:2,roster:[],playerRoster:[],futureFeature:{enabled:true}}),
  /newer than supported/
);

const once=migrateSave({saveVersion:0,roster:[],playerRoster:[],unknownFutureField:{kept:true}});
assert.deepStrictEqual(migrateSave(once),once);
assert.deepStrictEqual(once.unknownFutureField,{kept:true});
assert.deepStrictEqual(
  createPersistedSave({roster:[],temporaryUiState:{open:true},cachedHtml:'<p>cache</p>',domReferences:{node:'app'}}),
  {roster:[],saveVersion:1}
);
assert.throws(()=>migrateSave(null),/must be an object/);
assert.throws(()=>migrateSave({saveVersion:'one'}),/invalid saveVersion/);
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_application_uses_versioned_persistence_before_startup(self):
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "app.js").read_text()
        self.assertLess(index.index("persistence.js"), index.index("app.js"))
        self.assertIn("saveVersion:currentSaveVersion()", app)
        self.assertIn("return migrateSave(parsed)", app)
        self.assertIn("JSON.stringify(createPersistedSave(state))", app)
        self.assertIn("state.missionRuntime=objectiveEngine.getMissionRuntime()", app)
        self.assertIn("the original save was left unchanged", app)


if __name__ == "__main__":
    unittest.main()
