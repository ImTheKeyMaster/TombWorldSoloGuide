import json
import subprocess
import unittest
from pathlib import Path
from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def node(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class Stage7ManualDiceResumeTests(unittest.TestCase):
    def test_pending_dice_normalization_persistence_reset_and_old_saves(self):
        result = node("""
const p=require('./persistence.js');
const partial={version:1,requestKey:'combat:a:attack',status:'collecting',count:4,sides:6,title:'ATTACK ROLL',instruction:'Roll 4D6',rollerLabel:'Deathwatch',values:[6,3],resumeKind:'combat',resumeData:{activationId:'a'}};
const valid=p.normalizePendingDice(partial,'pvp');
const supportedD4=p.normalizePendingDice({...partial,count:2,sides:4,values:[4]},'pvp');
const old=p.migrateSave({saveVersion:3,gameMode:'pvp',roster:[],playerRoster:[]});
const saved=p.createPersistedSave({saveVersion:3,gameMode:'pvp',pendingDice:partial,roster:[]});
const reset=p.resetActiveBattle({gameMode:'pvp',pendingDice:partial,roster:[],journal:[]});
const malformed=[
  {...partial,values:[1,2,3,4,5]}, {...partial,values:[7]}, {...partial,sides:3,values:[4]},
  {...partial,values:[-1]}, {...partial,values:[1.5]}, {...partial,status:'committed'},
  {...partial,requestKey:''}, {...partial,sides:8}, {...partial,resumeKind:'unknown'}
].map(value=>p.normalizePendingDice(value,'pvp'));
process.stdout.write(JSON.stringify({valid,supportedD4,old:old.pendingDice,saved:saved.pendingDice,reset:reset.pendingDice,malformed,solo:p.normalizePendingDice(partial,'solo'),version:p.currentSaveVersion()}));
""")
        self.assertEqual(result["valid"]["values"], [6, 3])
        self.assertEqual(result["supportedD4"]["values"], [4])
        self.assertIsNone(result["old"])
        self.assertEqual(result["saved"]["values"], [6, 3])
        self.assertIsNone(result["reset"])
        self.assertEqual(result["malformed"], [None] * 9)
        self.assertIsNone(result["solo"])
        self.assertEqual(result["version"], 3)

    def test_provider_has_two_phase_exact_buffer_lifecycle(self):
        provider = APP[APP.index("let activeManualDiceRequest") : APP.index("diceEntryUndo.addEventListener")]
        self.assertIn("status='collecting'", provider)
        self.assertIn("persistManualDice(active,'committed')", provider)
        self.assertLess(provider.index("persistManualDice(active,'committed')"), provider.index("resolve(results)"))
        self.assertIn("if(!persistManualDice(active)){active.values.pop();return false;}", provider)
        self.assertIn("if(!persistManualDice(active)){active.values.push(value);return false;}", provider)
        self.assertIn("if(!persistManualDice(active,'committed')){active.committed=false", provider)
        self.assertIn("if(!persistManualDice(activeManualDiceRequest))throw new Error", provider)
        self.assertIn("state.pendingDice=previousPending", provider)
        self.assertIn("requestManualDiceResults(validatedRequest,pending.values)", provider)
        self.assertIn("if(pending.status==='committed')return pending.values.slice()", provider)
        self.assertIn("pending.count===request.count&&pending.sides===request.sides", provider)
        self.assertIn("A different manual dice request is already pending", provider)
        self.assertIn("state.pendingDice=null;save();return true", provider)

    def test_restoration_dispatches_to_existing_workflows(self):
        resume = APP[APP.index("function pendingDiceContextIsCurrent") : APP.index("async function missionDiceTotal")]
        for kind in ("strategy", "event", "player-activation", "breach-sarcophagus", "npo-special-action"):
            self.assertIn(f"pending.resumeKind==='{kind}'", resume)
        for entry in ("finishTurningPointStart()", "beginCurrentEvent()", "completePlayerActivation", "performBreachSarcophagus", "resolveNpoSpecialAction"):
            self.assertIn(entry, resume)
        self.assertIn("resolvePendingPlayerAttacks({...state.combatState.stage})", resume)
        self.assertIn("continueHumanNecronActivation()", resume)
        self.assertIn("if(state.pendingDice)await resumePendingDiceWorkflow()", APP)
        self.assertIn("['searchRoll','awakenRoll','directionRoll','distanceRoll'].includes(operationId)", resume)
        self.assertIn("return resumeMissionActionContext()", resume)
        self.assertIn("const operationId=data.operationId||data.resultId", resume)
        self.assertIn("operationId==='repairRoll'){await continueTurningPointStart()", resume)
        self.assertIn("state.hotResolution?.id!==data.hotResolutionId", resume)
        self.assertIn("state.hotResolution.acknowledged", resume)
        self.assertIn("state.lastActivation.pendingAction.id!==data.actionId", resume)
        self.assertIn("state.missionActionContext?.missionId!==state.missionId", resume)
        self.assertIn("missionActivationId('player',operativeId)!==data.activationId", resume)
        self.assertIn("state.missionActionContext.actionId!==expectedAction", resume)
        self.assertIn("state.pendingDice=null;save();\n      return resumeCheckpointedGameplayContext()", resume)
        startup_resume = APP[APP.index("async function resumeMissionActionContext") : APP.index("async function missionDiceTotal")]
        self.assertIn("performLocateItem(context.siteId,context.operativeId)", startup_resume)
        self.assertIn("performAwakenRoom(context.roomId)", startup_resume)
        self.assertIn("performAuspexCalibration()", startup_resume)
        self.assertIn("performBreachSarcophagus({...state.combatState.stage},true)", startup_resume)
        self.assertIn("state.strategyPipeline?.current==='mission-ready-hooks'", APP)
        self.assertIn("if(data.targetId)", resume)
        self.assertIn("state.playerCasualtyIds.includes(playerId)", resume)
        imported = APP[APP.index("async function commitImported") : APP.index("function showRegenerationNotice")]
        self.assertIn("if(state.pendingDice)await resumePendingDiceWorkflow()", imported)
        new_game = APP[APP.index("function startNewGameSetup") : APP.index("function confirmNewGame")]
        self.assertIn("discardActiveManualDiceRequest()", new_game)
        self.assertIn("resumeNpoSpecialActionContext()", APP)
        checkpointed = APP[APP.index("async function resumeCheckpointedGameplayContext") : APP.index("async function missionDiceTotal")]
        self.assertIn("resolvePendingPlayerAttacks({...state.combatState.stage})", checkpointed)
        self.assertIn("continueHumanNecronActivation()", checkpointed)
        self.assertIn("pendingAction?.diceResults", checkpointed)
        self.assertIn("['initiative','event'].includes(state.strategyPipeline?.current)", checkpointed)

    def test_every_gameplay_request_has_stable_identity_and_resume_metadata(self):
        calls = []
        cursor = APP.index("async function missionDiceTotal")
        while True:
            index = APP.find("requestDiceResults({", cursor)
            if index < 0:
                break
            end = APP.find("})", index)
            calls.append(APP[index:end + 2])
            cursor = end + 2
        self.assertGreaterEqual(len(calls), 18)
        for call in calls:
            self.assertIn("requestKey", call)
            self.assertIn("resumeKind", call)
            self.assertIn("resumeData", call)

    def test_required_consumers_are_keyed_and_checkpointed(self):
        for marker in (
            "subjugation-glyphs", "living-metal-flux", "maze-reforms", "initiative:tp",
            "reanimation-protocols", "aggressive-defence", "threat", "dimensional-banishment",
            "'attack'", "'defense'", "HOT TEST", "countertemporal-shifting",
            "geomantic-disturbance", "nanoscarab-beam", "breach-sarcophagus"
        ):
            self.assertIn(marker, APP)
        self.assertGreaterEqual(APP.count("acknowledgeDiceRequest("), 10)
        self.assertGreaterEqual(APP.count("acknowledgeCurrentDiceRequest()"), 5)

    def test_reviewed_sequence_keys_and_checkpoint_order_are_safe(self):
        combat = APP[APP.index("function runAutomaticCombatRolls") : APP.index("function retainedDiceTotals")]
        self.assertIn("requestKeyBase", combat)
        self.assertIn("acknowledgeDiceRequest(`${requestKeyBase}:attack`)", combat)
        self.assertIn("acknowledgeDiceRequest(`${requestKeyBase}:defense`)", combat)
        npo = APP[APP.index("function showNpoAttackWizard") : APP.index("async function animateMissionDice")]
        self.assertIn(":${n.id}:${target.id}:${profile.weaponId}:${profile.profileId}`", npo)
        breach = APP[APP.index("async function performBreachSarcophagus") : APP.index("function confirmMissionAction")]
        self.assertLess(breach.index("context.committed=true"), breach.index("acknowledgeDiceRequest(requestKey)"))
        mission = APP[APP.index("async function performLocateItem") : APP.index("function missionFeatureIdentity")]
        self.assertIn("siteId,operativeId:carrierId", mission)
        self.assertIn("actionId,roomId", mission)
        mission_number = APP[APP.index("function requestMissionNumber") : APP.index("async function runMissionEvent")]
        self.assertIn("state.missionReadyContext?.turningPoint===state.turningPoint", mission_number)
        self.assertIn("sarcophagusControllers:value", mission_number)
        mission_dice = APP[APP.index("async function animateMissionDice") : APP.index("function requestMissionNumber")]
        self.assertIn("previousPending.requestKey!==requestKey", mission_dice)
        self.assertNotIn("save();acknowledgeDiceRequest(requestKey)", mission_dice)
        special = APP[APP.index("function resolveNpoSpecialAction") : APP.index("function finishNpoSpecialAction")]
        self.assertIn("pendingAction.resolvedResult=resolvedResult", special)
        self.assertIn("pendingAction.resolvedResult=result", special)
        self.assertIn("previousPending.requestKey!==requestKey", mission_dice)

    def test_versions_and_existing_silent_mobile_dialog_are_preserved(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
        provider = APP[APP.index("let activeManualDiceRequest") : APP.index("diceEntryUndo.addEventListener")]
        self.assertNotIn("TombWorldDiceSfx", provider)
        self.assertNotIn("animated-roll", provider)
        self.assertIn("pendingDice:null", APP[APP.index("const initialState") : APP.index("const loadedSave")])

    def test_export_preserves_checkpointed_mission_dice(self):
        export_save = APP[APP.index("function exportSave") : APP.index("async function commitImported")]
        self.assertIn("const pendingDiceResults=state.missionRuntime?.pendingDiceResults", export_save)
        self.assertIn("state.missionRuntime.pendingDiceResults=pendingDiceResults", export_save)
        self.assertLess(export_save.index("state.missionRuntime.pendingDiceResults=pendingDiceResults"), export_save.index("createPersistedSave(state)"))


if __name__ == "__main__":
    unittest.main()
