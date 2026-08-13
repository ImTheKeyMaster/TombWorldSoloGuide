import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
CSS = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


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


class V707ReleaseValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definitions = npo_definitions()

    def test_catalog_is_exactly_the_seven_box_types_and_twenty_one_models(self):
        expected = {
            "Geomancer": 1,
            "Canoptek Tomb Crawler": 2,
            "Canoptek Macrocyte Warrior": 3,
            "Canoptek Macrocyte Accelerator": 1,
            "Canoptek Macrocyte Reanimator": 1,
            "Necron Warrior": 10,
            "Canoptek Scarab Swarm": 3,
        }
        self.assertEqual(
            {name: profile["physicalQuantity"] for name, profile in self.definitions.items()},
            expected,
        )
        self.assertEqual(sum(expected.values()), 21)
        self.assertEqual(len({profile["id"] for profile in self.definitions.values()}), 7)

    def test_profiles_loadouts_and_data_driven_rules_remain_available(self):
        expected_profiles = {
            "Geomancer": (3, 6, 3, 14),
            "Canoptek Tomb Crawler": (2, 5, 3, 21),
            "Canoptek Macrocyte Warrior": (2, 7, 4, 7),
            "Canoptek Macrocyte Accelerator": (2, 7, 4, 7),
            "Canoptek Macrocyte Reanimator": (2, 7, 4, 7),
        }
        for name, expected in expected_profiles.items():
            profile = self.definitions[name]
            self.assertEqual(
                (profile["apl"], profile["move"], profile["save"], profile["wounds"]),
                expected,
            )
        self.assertEqual(
            [item["id"] for item in self.definitions["Canoptek Tomb Crawler"]["loadoutOptions"]],
            ["twin-gauss-reapers", "transdimensional-isolator"],
        )
        self.assertEqual(
            [item["id"] for item in self.definitions["Canoptek Macrocyte Warrior"]["loadoutOptions"]],
            ["gauss-scalpel", "tesla-caster"],
        )
        rules = json.dumps(self.definitions)
        for rule in (
            "canoptek-control", "molecular-breach", "geomantic-disturbance",
            "dimensional-banishment", "aggressive-defence", "a-ceaseless-scuttling",
            "overcharge", "cranial-overload", "reanimate", "nanoscarab-beam",
        ):
            self.assertIn(rule, rules)

    def test_display_order_is_natural_without_mutating_gameplay_arrays(self):
        ordering = APP.split("function compareNpoDisplay", 1)[1].split(
            "function sortedNposForDisplay", 1
        )[0]
        sorter = APP.split("function sortedNposForDisplay", 1)[1].split("function ", 1)[0]
        self.assertIn("numeric:true,sensitivity:'base'", ordering)
        self.assertIn("return [...(Array.isArray(npos)?npos:[])]", sorter)
        self.assertIn("compareNpoDisplayNames", sorter)
        self.assertIn("state.activationHistory.unshift", APP)

    def test_continue_game_uses_the_migrated_state_payload(self):
        home = APP.split("function renderHome", 1)[1].split("function renderHowItWorks", 1)[0]
        self.assertIn("const saved=load()", home)
        self.assertIn("saved?.report?.requiresRegeneration?null:saved?.state", home)
        self.assertIn("savedGame?.missionId&&savedGame?.screen==='game'", home)
        self.assertIn("state=normalizeState(savedGame)", home)
        self.assertNotIn("load()?.missionId", home)

    def test_current_export_round_trip_is_canonical_and_idempotent(self):
        catalog = json.dumps(self.definitions)
        script = f"""
const assert=require('assert');
const persistence=require('./persistence.js');
const catalog={catalog};
const roster=Object.values(catalog).map((definition,index)=>({{
  id:`${{definition.id}}-${{index+1}}`, type:definition.type, name:definition.name,
  weaponId:definition.defaultWeaponId, wounds:definition.wounds, maxWounds:definition.wounds
}}));
const state={{version:'8.6.25',saveVersion:persistence.currentSaveVersion(),missionId:'01',
  roster,playerRoster:['player-1'],journal:[{{text:'completed history'}}]}};
const exported=persistence.createPersistedSave(state);
const imported=persistence.migrateSaveDetailed(JSON.parse(JSON.stringify(exported)),catalog);
assert.equal(imported.report.outcome,'current');
const repeated=persistence.migrateSaveDetailed(JSON.parse(JSON.stringify(imported.state)),catalog);
assert.equal(repeated.report.outcome,'current');
assert.deepEqual(repeated.state,imported.state);
assert.equal(new Set(imported.state.roster.map(npo=>npo.id)).size,7);
assert.ok(imported.state.roster.every(npo=>catalog[npo.type]));
assert.ok(imported.state.roster.every(npo=>!('portrait' in npo)&&!('matrixActive' in npo)));
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_portraits_and_matrix_gameplay_remain_absent_but_required_assets_exist(self):
        production = "\n".join((ROOT / name).read_text() for name in (
            "app.js", "index.html", "styles.css", "service-worker.js", "manifest.webmanifest"
        ))
        self.assertNotRegex(production, r"Assets/Images/Canoptek Circle|npoPortrait")
        self.assertNotRegex(json.dumps(self.definitions), r"(?i)obelisk|matrix")
        self.assertIn("eliminated-necron-skull.png", CSS)
        self.assertTrue((ROOT / "Assets/Images/eliminated-necron-skull.png").is_file())
        for asset in re.findall(r"'\./([^']+)'", WORKER):
            self.assertTrue((ROOT / asset).exists(), asset)

    def test_service_worker_install_and_activation_complete(self):
        script = r"""
const assert=require('assert');
const fs=require('fs');
const vm=require('vm');
const listeners={};
const added=[];
const deleted=[];
const context={
  URL,Request,Response,
  self:{addEventListener:(name,handler)=>{listeners[name]=handler;},clients:{claim:async()=>{}}},
  caches:{
    open:async name=>({
      addAll:async assets=>{added.push({name,assets});},
      add:async()=>{},
      match:async path=>new Response(JSON.stringify(path.includes('narration-manifest')?{entries:{}}:{landscape:['Landscape-01.png']}),{status:200})
    }),
    keys:async()=>['tomb-world-solo-guide-7.0.6','unrelated-cache'],
    delete:async name=>{deleted.push(name);return true;},
    match:async()=>undefined
  },
  fetch:async()=>new Response('ok',{status:200})
};
vm.runInNewContext(fs.readFileSync('service-worker.js','utf8'),context);
const dispatch=async name=>{
  let pending;
  listeners[name]({waitUntil:promise=>{pending=promise;}});
  await pending;
};
(async()=>{
  await dispatch('install');
  assert.equal(added.length,2);
  assert.equal(added[0].name,'tomb-world-solo-guide-8.6.64');
  assert.ok(added[0].assets.includes('./index.html'));
  assert.ok(added[0].assets.includes('./app.js?v=8.6.64'));
  assert.deepEqual(added[1].assets,['./Assets/Images/Backgrounds/Landscape-01.png']);
  await dispatch('activate');
  assert.deepEqual(deleted,['tomb-world-solo-guide-7.0.6']);
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_release_version_help_and_accessible_elimination_text_are_current(self):
        self.assertIn("const APP_VERSION = '8.6.64';", APP)
        self.assertIn("const APP_VERSION = '8.6.64';", WORKER)
        self.assertIn("V8.6.64", INDEX)
        for asset in ("app.js", "mission-engine.js", "persistence.js", "styles.css"):
            self.assertIn(f"{asset}?v=8.6.64", INDEX)
        self.assertIn("Tomb World NPO roster", APP)
        self.assertIn("NPO portraits are intentionally not displayed", APP)
        roster_card = APP.split("function npoRosterCard", 1)[1].split("function operativeCard", 1)[0]
        self.assertIn("eliminated?'ELIMINATED'", roster_card)
        self.assertIn("WOUNDS", roster_card)
        self.assertNotIn("<img", roster_card)


if __name__ == "__main__":
    unittest.main()
