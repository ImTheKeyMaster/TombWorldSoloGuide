import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def npo_definitions():
    source = APP.split("const npoDefinitions = ", 1)[1].split(
        ";\n\n  // Official 2D6 table", 1
    )[0]
    output = subprocess.check_output(
        ["node", "-e", f"const definitions={source}; process.stdout.write(JSON.stringify(definitions));"],
        cwd=ROOT,
        text=True,
    )
    return json.loads(output)


def run_node(body):
    result = subprocess.run(
        ["node", "-e", body], cwd=ROOT, text=True, capture_output=True
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)


class V741MigrationNoticeIdempotencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = npo_definitions()

    def test_current_numbered_warriors_and_full_inventory_are_unchanged(self):
        catalog = json.dumps(self.catalog)
        run_node(f"""
const assert=require('assert');
const p=require('./persistence.js');
const catalog={catalog};
const warriors=Array.from({{length:10}},(_,index)=>({{
  id:`necron-warrior-${{index+1}}`,type:'Necron Warrior',name:`Necron Warrior ${{index+1}}`,
  displayNumber:index+1,weaponId:index%2?'gauss-reaper':'gauss-flayer',wounds:9,maxWounds:9,
  move:5,apl:2,save:4,baseSize:32,deployed:index<5,battlefieldState:index<5?'deployed':'reserve'
}}));
const current={{saveVersion:p.currentSaveVersion(),version:'7.4.0',roster:warriors,
  playerRoster:[],journal:[{{text:'history remains'}}],activationHistory:[{{npoId:'necron-warrior-1'}}]}};
const first=p.migrateSaveDetailed(current,catalog);
assert.equal(first.report.outcome,'current');
assert.deepEqual(first.report.aliasesApplied,[]);
assert.deepEqual(first.report.instanceNamesRepaired,[]);
assert.deepEqual(first.state.roster,warriors);
const second=p.migrateSaveDetailed(first.state,catalog);
assert.equal(second.report.outcome,'current');
assert.deepEqual(second.report.aliasesApplied,[]);
assert.deepEqual(second.state,first.state);

let serial=0;
const full=[];
for(const definition of Object.values(catalog)){{
  for(let index=1;index<=definition.physicalQuantity;index++){{
    serial++;
    full.push({{id:`inventory-${{serial}}`,type:definition.type,
      name:definition.physicalQuantity>1?`${{definition.name}} ${{index}}`:definition.name,
      displayNumber:definition.physicalQuantity>1?index:null,
      weaponId:definition.defaultWeaponId,wounds:definition.wounds,maxWounds:definition.wounds,
      move:definition.move,apl:definition.apl,save:definition.save,baseSize:definition.baseSize,
      deployed:index%2===1,battlefieldState:index%2===1?'deployed':'reserve'}});
  }}
}}
assert.equal(full.length,21);
const fullSave={{saveVersion:p.currentSaveVersion(),roster:full,playerRoster:[],
  journal:[{{text:'preserved'}}],activationHistory:[{{npoId:full[0].id}}]}};
const fullResult=p.migrateSaveDetailed(fullSave,catalog);
assert.equal(fullResult.report.outcome,'current');
assert.deepEqual(fullResult.report.aliasesApplied,[]);
assert.deepEqual(fullResult.report.invalidPhysicalLimits,[]);
assert.deepEqual(fullResult.state.roster,full);
assert.deepEqual(fullResult.state.journal,fullSave.journal);
assert.deepEqual(fullResult.state.activationHistory,fullSave.activationHistory);
""")

    def test_alias_and_missing_name_repair_once_without_false_aliases(self):
        catalog = json.dumps(self.catalog)
        run_node(f"""
const assert=require('assert');
const p=require('./persistence.js');
const catalog={catalog};
const alias={{saveVersion:3,roster:[{{id:'macrocyte-1',type:'Canoptek Macrocyte',
  name:'Canoptek Macrocyte',displayNumber:1,weaponId:'gauss-scalpel',wounds:7}}],playerRoster:[]}};
const first=p.migrateSaveDetailed(alias,catalog);
assert.equal(first.report.outcome,'migrated');
assert.equal(first.state.roster[0].type,'Canoptek Macrocyte Warrior');
assert.equal(first.report.aliasesApplied.length,1);
const second=p.migrateSaveDetailed(first.state,catalog);
assert.equal(second.report.outcome,'current');
assert.deepEqual(second.report.aliasesApplied,[]);
assert.deepEqual(second.state,first.state);

for(const missing of [undefined,'   ']){{
  const npo={{id:'warrior-1',type:'Necron Warrior',displayNumber:1,
    weaponId:'gauss-flayer',wounds:9}};
  if(missing!==undefined)npo.name=missing;
  const repaired=p.migrateSaveDetailed({{saveVersion:3,roster:[npo],playerRoster:[]}},catalog);
  assert.equal(repaired.report.outcome,'migrated');
  assert.deepEqual(repaired.report.aliasesApplied,[]);
  assert.equal(repaired.report.instanceNamesRepaired.length,1);
  assert.equal(repaired.state.roster[0].name,'Necron Warrior');
  const repeated=p.migrateSaveDetailed(repaired.state,catalog);
  assert.equal(repeated.report.outcome,'current');
  assert.deepEqual(repeated.report.instanceNamesRepaired,[]);
  assert.deepEqual(repeated.state,repaired.state);
}}
""")

    def test_other_real_repairs_remain_one_time_and_idempotent(self):
        catalog = json.dumps(self.catalog)
        run_node(f"""
const assert=require('assert');
const p=require('./persistence.js');
const catalog={catalog};
const legacy={{saveVersion:3,roster:[{{type:'Necron Warrior',name:'Necron Warrior 1',displayNumber:1,
  weaponId:'obsolete-gun',wounds:99,portraitUrl:'removed.png',matrixActive:true}}],playerRoster:[],
  obeliskNodeMatrix:{{active:true}},lastActivation:{{npoId:'missing-id'}}}};
const first=p.migrateSaveDetailed(legacy,catalog);
assert.equal(first.report.outcome,'migrated');
assert.equal(first.report.instanceIdsCreated.length,1);
assert.equal(first.report.loadoutsNormalized.length,1);
assert.equal(first.report.woundsClamped.length,1);
assert.ok(first.report.portraitFieldsRemoved>0);
assert.ok(first.report.matrixFieldsRemoved>0);
assert.deepEqual(first.report.pendingStateCleared,['lastActivation']);
assert.equal(first.state.roster[0].portraitUrl,undefined);
assert.equal(first.state.roster[0].matrixActive,undefined);
assert.equal(first.state.obeliskNodeMatrix,undefined);
const second=p.migrateSaveDetailed(first.state,catalog);
assert.equal(second.report.outcome,'current');
assert.deepEqual(second.state,first.state);
""")

    def test_startup_notice_is_gated_by_real_changes_and_successful_save(self):
        startup = APP.split("Promise.all([loadMissionPack(),loadPlayerManifest()])", 1)[1]
        imports = APP.split("importInput.addEventListener('change'", 1)[1].split(
            "function bindCommon", 1
        )[0]
        helper = APP.split("function hasMeaningfulMigrationChanges", 1)[1].split(
            "async function commitImported", 1
        )[0]
        self.assertIn("report?.outcome==='migrated'", helper)
        self.assertIn("report.instanceNamesRepaired.length", helper)
        self.assertIn("!storedMigrationNoticeShown&&hasMeaningfulMigrationChanges(loadedSave?.report)", startup)
        self.assertIn("if(save()){storedMigrationNoticeShown=true;showMigrationNotice(loadedSave.report);}", startup)
        self.assertNotIn("APP_VERSION", startup.split(".catch", 1)[0])
        self.assertIn("if(await commitImported", imports)
        self.assertIn("hasMeaningfulMigrationChanges(migration.report)", imports)
        self.assertNotIn("serviceWorker", helper + startup.split(".catch", 1)[0])


if __name__ == "__main__":
    unittest.main()
