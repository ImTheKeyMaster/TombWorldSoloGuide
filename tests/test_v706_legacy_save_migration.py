import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V706LegacySaveMigrationTests(unittest.TestCase):
    def test_migration_outcomes_aliases_profiles_inventory_and_cleanup(self):
        script = r"""
const assert=require('assert');
const p=require('./persistence.js');
const catalog={
  'Canoptek Tomb Crawler':{id:'canoptek-tomb-crawler',type:'Canoptek Tomb Crawler',name:'Canoptek Tomb Crawler',physicalQuantity:2,wounds:21,move:5,apl:2,save:3,baseSize:50,defaultWeaponId:'twin-gauss-reapers',loadoutOptions:[{id:'twin-gauss-reapers',name:'Twin gauss reapers and claws'},{id:'transdimensional-isolator',name:'Transdimensional isolator and claws'}]},
  'Canoptek Macrocyte Warrior':{id:'canoptek-macrocyte-warrior',type:'Canoptek Macrocyte Warrior',name:'Canoptek Macrocyte Warrior',physicalQuantity:3,wounds:7,move:7,apl:2,save:4,baseSize:28,defaultWeaponId:'gauss-scalpel',loadoutOptions:[{id:'gauss-scalpel',name:'Gauss scalpel and claws & tail'},{id:'tesla-caster',name:'Tesla caster and claws & tail'}]}
};
const current={saveVersion:3,roster:[{id:'crawler-1',type:'Canoptek Tomb Crawler',name:'Canoptek Tomb Crawler',displayNumber:1,weaponId:'twin-gauss-reapers',wounds:12,maxWounds:21,move:5,apl:2,save:3,baseSize:50}],playerRoster:[]};
const currentResult=p.migrateSaveDetailed(current,catalog);
assert.equal(currentResult.report.outcome,'current');
assert.equal(currentResult.state.roster[0].id,'crawler-1');
assert.equal(currentResult.state.roster[0].wounds,12);

const legacy={saveVersion:2,roster:[{type:'  canoptek   macrocyte ',name:'Old',weaponName:'Tesla caster',wounds:99,portraitPath:'gone.png',matrixDerivedApl:1}],playerRoster:['player'],playerOperativeStates:{player:{inPlay:true,portrait:'keep.png'}},journal:[{result:'won',npo:'Retired Sentinel'}],obeliskNodeMatrix:{active:true}};
const migrated=p.migrateSaveDetailed(legacy,catalog);
assert.equal(migrated.report.outcome,'migrated');
assert.equal(migrated.state.roster[0].type,'Canoptek Macrocyte Warrior');
assert.equal(migrated.state.roster[0].weaponId,'tesla-caster');
assert.equal(migrated.state.roster[0].wounds,7);
assert.match(migrated.state.roster[0].id,/^legacy-/);
assert.equal(migrated.state.roster[0].portraitPath,undefined);
assert.equal(migrated.state.obeliskNodeMatrix,undefined);
assert.equal(migrated.state.playerOperativeStates.player.portrait,'keep.png');
assert.equal(migrated.state.journal[0].npo,'Retired Sentinel');
assert.ok(migrated.report.matrixFieldsRemoved>=2);
assert.deepStrictEqual(p.migrateSaveDetailed(migrated.state,catalog).state,migrated.state);

const retired=p.migrateSaveDetailed({saveVersion:2,roster:[{id:'old',type:'Crypt Sentinel'}],playerRoster:[]},catalog);
assert.equal(retired.report.outcome,'regeneration-required');
assert.deepEqual(retired.report.unsupportedRetiredTypes,['Crypt Sentinel']);
assert.equal(retired.state.roster[0].type,'Crypt Sentinel');

const excess=p.migrateSaveDetailed({saveVersion:2,roster:[1,2,3].map(i=>({id:`crawler-${i}`,type:'Canoptek Tomb Crawler',weaponId:'twin-gauss-reapers',wounds:21}))},catalog);
assert.equal(excess.report.requiresRegeneration,true);
assert.ok(excess.report.invalidPhysicalLimits.length);

const reset=p.resetActiveBattle({...retired.state,missionId:'04',playerRoster:['player'],journal:[{text:'uncommitted'}],settings:{sound:false},turningPoint:3,missionRuntime:{active:true},npoRuleState:{aplModifiers:[{ruleId:'overcharge'}]}});
assert.equal(reset.turningPoint,0);assert.deepEqual(reset.roster,[]);assert.equal(reset.missionId,'04');assert.deepEqual(reset.playerRoster,['player']);assert.deepEqual(reset.journal,[]);assert.equal(reset.missionRuntime,null);assert.deepEqual(reset.npoRuleState.aplModifiers,[]);assert.deepEqual(reset.settings,{sound:false});
const completedReset=p.resetActiveBattle({...retired.state,completed:true,journal:[{result:'won'}]});
assert.deepEqual(completedReset.journal,[{result:'won'}]);
const exported=p.createPersistedSave({...migrated.state,roster:[{...migrated.state.roster[0],portrait:'gone',obeliskMatrix:true}]});
assert.equal(exported.saveVersion,3);assert.equal(exported.roster[0].portrait,undefined);assert.equal(exported.roster[0].obeliskMatrix,undefined);
assert.equal(p.migrateSaveDetailed(exported,catalog).report.outcome,'current');
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_ui_transaction_and_release_guards(self):
        app = (ROOT / "app.js").read_text()
        persistence = (ROOT / "persistence.js").read_text()
        self.assertIn("NPO roster updated for v7", app)
        self.assertIn("Current battle cannot be resumed", app)
        self.assertIn("confirmLegacyReset", app)
        self.assertIn("const previous=state", app)
        self.assertIn("state=previous", app)
        self.assertIn("migrateSaveDetailed(data,npoDefinitions)", app)
        self.assertNotIn("TODO(v7 legacy-save migration)", app)
        self.assertIn("const RETIRED_NPO_TYPES = Object.freeze([])", persistence)
        self.assertEqual(persistence.count("'canoptek macrocyte':"), 1)
        self.assertIn("const APP_VERSION = '7.2.0';", app)


if __name__ == "__main__":
    unittest.main()
