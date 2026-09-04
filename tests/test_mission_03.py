import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Mission03Tests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_loading_search_completion_lifecycle_hud_details_and_restore(self):
        self.run_node(r"""
const assert=require('assert').strict;const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-03-recover-transponder.json'));
(async()=>{
  api.validateMissionDefinition(definition);
  const rolls=[{dice:[1],total:1},{dice:[3],total:3}];
  const escaped=[];
  const engine=api.createMissionEngine({requestDiceRoll:async()=>rolls.shift(),setOperativeInPlay:async operation=>{escaped.push(operation);return true;}});
  const runtime=engine.initializeMissionRuntime(definition,{turningPoint:1,now:()=> '2026-07-22T00:00:00Z'});
  assert.equal(engine.getObjectiveValue('transponderRecovered'),0);
  assert.deepEqual(engine.getMissionHudModel(),{missionId:'03',name:'Recover Transponder',label:'MISSION',objectiveId:'transponderRecovered',value:0,target:1,completed:false,visible:true});
  for(const hook of ['onMissionInitialized','onStrategyPhaseReadyStep','onPlayerActivationStarted','onPlayerActivationCompleted','onNpoActivationStarted','onNpoActivationCompleted','onTurningPointEnded','onBattleEnded']){
    assert.deepEqual(await engine.executeMissionHook(hook,{turningPoint:1,activationId:'one'}),[]);
  }
  const first=await engine.executeMissionAction('searchTransponder',{turningPoint:1,phase:'firefight',activationId:'activation-one',operativeId:'alpha'});
  assert.equal(first.results.searchRoll.total,1);assert.equal(engine.getObjectiveValue('transponderRecovered'),0);
  assert.equal((await engine.executeMissionAction('searchTransponder',{turningPoint:1,phase:'firefight',activationId:'activation-one',operativeId:'alpha'})).status,'already-executed');
  const second=await engine.executeMissionAction('searchTransponder',{turningPoint:2,phase:'firefight',activationId:'activation-two',operativeId:'alpha'});
  assert.equal(second.results.searchRoll.total,3);assert.equal(engine.getMissionDetailsModel().history.length,2);
  const completion=await engine.executeMissionAction('recordTransponderEscape',{turningPoint:2,phase:'firefight',operativeId:'alpha'});
  assert.deepEqual(escaped,[{side:'player',operativeId:'alpha',inPlay:false,reason:'escaped'}]);
  assert.deepEqual(completion.changes[0],{objectiveId:'transponderRecovered',before:0,after:1});
  assert.equal(runtime.objectives.transponderRecovered.completed,true);assert.equal(runtime.objectives.transponderRecovered.completedTurningPoint,2);
  assert.equal(engine.getMissionHudModel().completed,true);assert.equal(definition.completion.endsBattle,true);
  assert.deepEqual(runtime.history.at(-1).completedObjectiveIds,['transponderRecovered']);
  assert.equal((await engine.executeMissionAction('recordTransponderEscape',{turningPoint:2,phase:'firefight',operativeId:'alpha'})).status,'unavailable');
  assert.equal(escaped.length,1);
  assert.equal((await engine.executeMissionAction('searchTransponder',{turningPoint:2})).status,'unavailable');
  const saved=JSON.parse(JSON.stringify(runtime));
  const refreshed=api.createMissionEngine();refreshed.restoreMissionRuntime(definition,saved,{turningPoint:2});
  assert.equal(refreshed.getObjectiveValue('transponderRecovered'),1);assert.equal(refreshed.getMissionHudModel().completed,true);
  assert.equal(refreshed.getMissionDetailsModel().history.length,3);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_locate_item_comparison_for_every_remaining_marker_case(self):
        self.run_node(r"""
const assert=require('assert').strict;require('./mission-engine.js');
const resolve=globalThis.TombWorldMissionEngine.resolveRemainingEntityRoll;
assert.deepEqual([1,2,3].map(roll=>resolve(roll,3).found),[false,false,true]);
assert.deepEqual([1,2,3].map(roll=>resolve(roll,2).found),[false,true,true]);
assert.deepEqual([1,2,3].map(roll=>resolve(roll,1).found),[true,true,true]);
assert.equal(resolve(2,3).otherRemainingMarkerCount,2);
assert.equal(resolve(2,2).otherRemainingMarkerCount,1);
assert.equal(resolve(1,1).otherRemainingMarkerCount,0);
""")

    def test_final_marker_bypasses_selection_and_dice_but_uses_action_transaction(self):
        app=(ROOT/'app.js').read_text()
        locate=app[app.index('async function performLocateItem'):app.index('function showUpdateTransponderCarrier')]
        selection=app[app.index("if(action.id==='pickUpMarker')"):app.index("const descriptions=",app.index("if(action.id==='pickUpMarker')"))]

        self.assertIn("const automatic=available.length===1",locate)
        self.assertIn("const outcome=automatic?null:objectiveEngine?",locate)
        self.assertIn("const result=automatic?null:await missionDiceTotal",locate)
        self.assertIn("const found=automatic||TombWorldMissionEngine.resolveRemainingEntityRoll",locate)
        self.assertIn("if(!commitHumanPlayerAction(stage,{deferContinuation:true}))return",locate)
        self.assertIn("...(result===null?{}:{roll:result})",locate)
        self.assertIn("progress.lastRoll={siteId,...(result===null?{}:{roll:result})",locate)
        self.assertIn("else if(automatic)objectiveEngine?.recordMissionHistory",locate)
        self.assertIn("const diceResult=result===null?'':",locate)
        self.assertNotIn("pendingDice=",locate)

        self.assertIn("if(available.length===1){void performLocateItem(available[0].id,activation.operativeId,stage);return;}",selection)
        self.assertLess(selection.index("if(available.length===1)"),selection.index("showModal('LOCATE ITEM'"))
        self.assertIn("if(!available.length)",selection)
        self.assertIn("cancelCurrentHumanPlayerAction()",selection)
        self.assertIn("Saved mission state was preserved",selection)

    def test_searching_state_is_not_promoted_when_only_one_marker_remains(self):
        app=(ROOT/'app.js').read_text()
        normalizer=app[app.index("}else if(engine.type==='transponder'){"):app.index("}else if(engine.type==='destruction'){")]
        locate=app[app.index('async function performLocateItem'):app.index('function showUpdateTransponderCarrier')]
        hud=app[app.index('function missionHudHtml'):app.index('const missionProgressRenderers')]

        self.assertIn("normalized.transponderFound=Boolean(raw.transponderFound||foundEntry||raw.escaped)",normalizer)
        self.assertIn("normalized.searchSitesResolved=normalized.transponderFound?engine.sites.length",normalizer)
        self.assertIn("}else progress.searchSitesResolved=missionEngine().sites.filter",locate)
        self.assertIn("transponder.transponderFound?'TRANSPONDER FOUND':`SEARCH",hud)
        self.assertNotIn("available.length===1",normalizer)
        self.assertNotIn("available.length===1",hud)

    def test_complete_activation_dice_carrier_persistence_and_outcome_contracts(self):
        app=(ROOT/'app.js').read_text()
        definition=json.loads((ROOT/'Missions/definition-03-recover-transponder.json').read_text())
        runtime=definition['runtime']['initial']
        self.assertEqual([marker['initialState'] for marker in definition['runtime']['markers']],['available']*3)
        self.assertFalse(runtime['transponderFound'])
        self.assertIsNone(runtime['carrierOperativeId'])
        self.assertEqual(runtime['transponderStatus'],'unknown')
        self.assertEqual(runtime['searchSitesResolved'],0)
        self.assertEqual(definition['actions'][0]['diceExpression'],'1D3')
        self.assertEqual(definition['actions'][0]['comparison'],'roll > otherRemainingMarkerCount')
        self.assertEqual(definition['actions'][0]['oncePer'],'activation')
        self.assertEqual(definition['actions'][1]['oncePer'],'game')
        self.assertEqual(definition['actions'][1]['operations'][0],{'type':'setOperativeInPlay','side':'player','operativeIdFrom':'operativeId','inPlay':False,'reason':'escaped'})
        for contract in (
            "name:'Pick Up Marker'", "cost:Number(objectiveDefinition", "performLocateItem(button.dataset.locateSite",
            "commitHumanPlayerAction(stage,{deferContinuation:true})", "resumeKind:'mission'", "transactionId",
            "transponderStatus='onBattlefield'", "showUpdateTransponderCarrier", "confirmTransponderEscape",
            "completeMission('victory')", "handleTransponderCarrierIncapacitation", "livingPlayerOperativeCount()===0"
        ):
            self.assertIn(contract,app)
        self.assertNotIn("Math.random()",app[app.index('async function performLocateItem'):app.index('async function performAwakenRoom')])
        self.assertIn("progress.transponderFound=true",app)
        self.assertIn("progress.searchSitesResolved=missionEngine().sites.length",app)
        self.assertIn("if(found){",app)
        self.assertNotIn("completeMission",app[app.index('if(found){',app.index('async function performLocateItem')):app.index('}else progress.searchSitesResolved',app.index('async function performLocateItem'))])

    def test_migration_and_idempotency_fields_are_durable(self):
        app=(ROOT/'app.js').read_text()
        normalizer=app[app.index("}else if(engine.type==='transponder'){"):app.index("}else if(engine.type==='destruction'){")]
        for field in ('transponderFound','transponderMarkerId','carrierId','transponderStatus','searchSitesResolved','extractionConfirmed','completed','outcome','transactions','lastRoll'):
            self.assertIn(f'normalized.{field}',normalizer)
        self.assertIn("{found:'transponder',empty:'cleared'}",normalizer)
        self.assertIn("normalized.sites[site.id]='removed'",normalizer)
        self.assertIn("missionEngine(savedMission)?.type==='transponder'",app)
        self.assertIn("progress.transactions?.[transactionId]",app)
        self.assertIn("if(progress.transactions?.[transactionId]||state.gameEnd)return",app)

    def test_registry_ui_persistence_offline_and_reference_regressions(self):
        manifest=json.loads((ROOT/'Missions/manifest.json').read_text())
        self.assertIn({'id':'03','file':'definition-03-recover-transponder.json'},manifest['definitions'])
        mission=json.loads((ROOT/'Missions/03-recover-transponder.json').read_text())
        self.assertEqual(len(mission['missionEngine']['sites']),3)
        app=(ROOT/'app.js').read_text();worker=(ROOT/'service-worker.js').read_text()
        self.assertIn("executeMissionAction('searchTransponder'",app)
        self.assertIn("executeMissionAction('recordTransponderEscape'",app)
        self.assertIn("if(missionEngine(selectedMission)?.type==='transponder')objectiveEngine.setObjectiveValue('transponderRecovered'",app)
        self.assertIn("'./Missions/definition-03-recover-transponder.json'",worker)
        self.assertIn('objectiveEngine.getMissionDetailsModel()',app)
        self.assertIn('missionHudHtml()',app)
        files=('definition-01-shifting-labyrinth.json','definition-02-demolition-protocol.json','definition-04-destroy-sarcophagus.json')
        for filename in files:
            self.assertTrue((ROOT/'Missions'/filename).exists())


if __name__ == '__main__':
    unittest.main()
