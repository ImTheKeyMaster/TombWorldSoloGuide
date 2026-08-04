import json
import pathlib
import re
import subprocess
import textwrap
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
DE=(ROOT/'deadly-encounters.js').read_text()
INDEX=(ROOT/'index.html').read_text()
README=(ROOT/'README.md').read_text()
PERSISTENCE=(ROOT/'persistence.js').read_text()
WORKER=(ROOT/'service-worker.js').read_text()
STYLES=(ROOT/'styles.css').read_text()

ROOM_NAMES=['Collapsed Ceiling','Darkness','Corrosive Fluid Leak','Energy Rupture','Airborne Virus','Accelerated/Decelerated Time','Crumbling Floor','Gravitic Anomaly','Unusual']
OBJECTIVE_NAMES=['Quantum Shield','Tesla Device','Teleportation Device','Control Node','Temporal Sphere','Hyperphase Aura','Regeneration Sphere','Amplification Matrix','Unusual']
RESULTS=['11','12','13','21','22','23','31','32','33']


def node(script):
    result=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True,check=True)
    return json.loads(result.stdout or 'null')

class DeadlyEncounterDefinitions(unittest.TestCase):
    def test_complete_unique_d33_tables(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(Object.fromEntries(Object.entries(d.tables).map(([k,v])=>[k,v.map(x=>x.result)]))))")
        self.assertEqual(data,{'room':RESULTS,'objective':RESULTS})
        self.assertEqual(len(set(data['room'])),9);self.assertEqual(len(set(data['objective'])),9)

    def test_official_names_match_attached_source(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify({room:d.tables.room.map(x=>x.name),objective:d.tables.objective.map(x=>x.name)}))")
        self.assertEqual(data['room'],ROOM_NAMES);self.assertEqual(data['objective'],OBJECTIVE_NAMES)

    def test_every_definition_has_required_metadata_and_handler(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(d.features))")
        for feature in data:
            for key in ['id','table','result','name','summary','duration','timing','affectedSides','requiredInput','automation','handler','cleanupTiming','source']:
                self.assertTrue(feature.get(key),f"{feature['name']} missing {key}")
            self.assertEqual(feature['source'],'White Dwarf 521, February 2026')
        self.assertNotRegex(DE,r'\b(?:TODO|FIXME|placeholder)\b')

    def test_stable_ids_are_unique_except_shared_unusual(self):
        ids=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(d.features.map(x=>x.id)))")
        self.assertEqual(ids.count('unusual'),2)
        self.assertEqual(len([x for x in ids if x!='unusual']),len(set(x for x in ids if x!='unusual')))

    def test_all_handlers_are_classified(self):
        self.assertTrue(node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(d.validateDefinitions()))"))
        self.assertTrue(node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(d.features.every(x=>typeof d.handlers[x.handler]==='function')))"))

class DeadlyEncounterD33(unittest.TestCase):
    def test_first_d3_is_tens_and_second_is_units(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify([[1,1],[1,2],[1,3],[2,1],[2,2],[2,3],[3,1],[3,2],[3,3]].map(x=>d.d33(...x))))")
        self.assertEqual(data,RESULTS)

    def test_invalid_d3_is_rejected(self):
        self.assertTrue(node("const d=require('./deadly-encounters.js');let ok=false;try{d.d33(4,1)}catch(e){ok=true}console.log(JSON.stringify(ok))"))

    def test_duplicate_feature_rerolls_battle_wide(self):
        script="""const d=require('./deadly-encounters.js');let s=d.emptyState();s.usedFeatureIds=['room-collapsed-ceiling'];let rolls=[1,1,1,2];let r=d.rollFeature(s,'room',()=>rolls.shift());console.log(JSON.stringify(r));"""
        data=node(script);self.assertEqual(data['featureIds'],['room-darkness']);self.assertEqual(data['attempts'][0]['status'],'discarded')

    def test_unusual_is_shared_between_tables(self):
        data=node("const d=require('./deadly-encounters.js');let s=d.emptyState();s.usedFeatureIds=['unusual'];let q=[3,3,1,1];let r=d.rollFeature(s,'objective',()=>q.shift());console.log(JSON.stringify(r));")
        self.assertEqual(data['attempts'][0]['status'],'discarded');self.assertEqual(data['featureIds'],['objective-quantum-shield'])

    def test_unusual_rolls_two_different_secondary_features(self):
        data=node("const d=require('./deadly-encounters.js');let q=[3,3,1,1,1,2];let r=d.rollFeature(d.emptyState(),'room',()=>q.shift());console.log(JSON.stringify(r));")
        self.assertTrue(data['unusual']);self.assertEqual(data['featureIds'],['room-collapsed-ceiling','room-darkness']);self.assertIn('unusual',data['state']['usedFeatureIds'])

    def test_secondary_33_and_used_results_reroll(self):
        data=node("const d=require('./deadly-encounters.js');let q=[3,3,3,3,1,1,1,1,1,2];let r=d.rollFeature(d.emptyState(),'room',()=>q.shift());console.log(JSON.stringify(r));")
        self.assertEqual(data['featureIds'],['room-collapsed-ceiling','room-darkness']);self.assertGreaterEqual(sum(x['status']=='discarded' for x in data['attempts']),2)

    def test_exhaustion_stops_without_reuse(self):
        data=node("const d=require('./deadly-encounters.js');let s=d.emptyState();s.usedFeatureIds=d.tables.room.map(x=>x.id);let r=d.rollFeature(s,'room',()=>1);console.log(JSON.stringify(r));")
        self.assertTrue(data['exhausted']);self.assertEqual(data['featureIds'],[]);self.assertIn('No unused official room feature',data['message'])

    def test_time_mode_is_rolled_once_and_persisted(self):
        script="""const d=require('./deadly-encounters.js');let s=d.registerRoom(d.emptyState(),{id:'r1',label:'Room 1',missionId:'05',dropZone:'none'});let c={missionId:'05',turningPoint:1,activationId:'a1',actionId:'x1',actingSide:'player',operativeId:'p1',triggerType:'opened',roomId:'r1',entityType:'room',entityId:'r1'};let q=[2,3];let a=d.discover(s,true,c,()=>q.shift(),()=>5);let b=d.normalizeState(JSON.parse(JSON.stringify(a.state)));console.log(JSON.stringify(b.rooms.r1.activeEffectState['room-accelerated-decelerated-time']));"""
        self.assertEqual(node(script),{'roll':5,'mode':'decelerated'})

    def test_idempotent_transaction_prevents_rerender_reload_and_rapid_taps(self):
        script="""const d=require('./deadly-encounters.js');let s=d.registerRoom(d.emptyState(),{id:'r1',label:'Room 1',missionId:'05',dropZone:'none'});let c={missionId:'05',turningPoint:1,activationId:'a1',actionId:'x1',actingSide:'player',operativeId:'p1',triggerType:'opened',roomId:'r1',entityType:'room',entityId:'r1'};let q=[1,1];let a=d.discover(s,true,c,()=>q.shift());let b=d.discover(a.state,true,c,()=>{throw Error('rerolled')});console.log(JSON.stringify({a:a.featureIds,b:b.featureIds,duplicate:b.duplicate,history:b.state.rollHistory.length}));"""
        data=node(script);self.assertEqual(data,{'a':['room-collapsed-ceiling'],'b':[],'duplicate':True,'history':1})

class DeadlyEncounterDiscovery(unittest.TestCase):
    def test_room_drop_zone_eligibility(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(['none','player','npo','both'].map(d.roomEligible)))")
        self.assertEqual(data,[True,False,True,True])

    def test_only_player_actions_create_discovery_checks(self):
        self.assertIn("context.actingSide!=='player'",DE)
        self.assertIn('NPOs never reveal them',APP)

    def test_first_room_interaction_wins_and_later_does_not_reroll(self):
        self.assertIn("!current.rooms[context.roomId].featureIds.length",DE)
        self.assertIn("['opened','entered']",DE)

    def test_first_marker_contest_or_control_wins(self):
        self.assertIn("['contested','controlled']",DE)
        self.assertIn("!current.objectives[context.objectiveId].featureIds.length",DE)

    def test_carrier_and_locations_are_normalized_and_persisted(self):
        self.assertIn('carrierId',DE);self.assertIn('operativeLocations',DE)
        self.assertIn('deadlyEncountersState',PERSISTENCE)

    def test_movement_pause_guidance_is_present(self):
        self.assertIn('Pause if this operative first enters an unexplored room.',DE)
        self.assertIn('Room entry interrupts movement',APP)

class DeadlyEncounterBriefingAndPersistence(unittest.TestCase):
    def test_optional_rules_and_classifications(self):
        self.assertIn('<h4>Optional Rules</h4>',APP);self.assertIn('House Rule',APP);self.assertIn('Official Expansion - White Dwarf 521',APP)
        self.assertNotIn('Optional House Rule',APP)

    def test_both_options_default_off_and_are_independent(self):
        self.assertIn('restlessTombEnabled:false, deadlyEncountersEnabled:false',APP)
        self.assertRegex(APP,r"#deadlyEncountersEnabled[^\n]+state\.deadlyEncountersEnabled")
        self.assertRegex(APP,r"#restlessTombEnabled[^\n]+state\.restlessTombEnabled")

    def test_active_game_settings_are_read_only(self):
        self.assertIn("<strong>Deadly Encounters:</strong> ${state.deadlyEncountersEnabled?'On':'Off'}",APP)
        self.assertNotIn('id="deadlyEncountersEnabled"',APP.split("function showDeadlyEncountersPanel",1)[1])

    def test_older_save_defaults_disabled_and_empty(self):
        self.assertIn('merged.deadlyEncountersEnabled=raw.deadlyEncountersEnabled===true',APP)
        self.assertIn('DeadlyEncounters.normalizeState(raw.deadlyEncountersState)',APP)

    def test_malformed_state_normalizes_safely(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify(d.normalizeState({version:99,rooms:{bad:1}})))")
        self.assertEqual(data['version'],1);self.assertEqual(data['rooms'],{})

    def test_export_import_uses_complete_state(self):
        self.assertIn('createPersistedSave(state)',APP);self.assertIn('deadlyEncountersState',PERSISTENCE)
        self.assertIn('pendingResolution',DE);self.assertIn('temporaryEffects',DE);self.assertIn('regenerationUsedBy',DE)

    def test_new_game_resets_both_options(self):
        self.assertIn('restlessTombEnabled:false,deadlyEncountersEnabled:false',PERSISTENCE)

class DeadlyEncounterIntegration(unittest.TestCase):
    def test_resolution_handlers_execute_feature_rules(self):
        data=node("const d=require('./deadly-encounters.js');console.log(JSON.stringify({room:d.handlers.applyRoomModifiers({move:6,normalDamage:4,criticalDamage:5,featureIds:['room-collapsed-ceiling','room-gravitic-anomaly','room-crumbling-floor']}),virus:d.handlers.checkAirborneVirus({actionType:'mission action',d6:5,apl:2}),regen:d.handlers.resolveRegeneration({contesting:true,usedThisBattle:false,d6:4}),amp:d.handlers.resolveAmplification({controlsMarker:true,enemyInControlRange:false,weaponId:'blade'})}))")
        self.assertEqual(data['room'],{'move':6,'normalDamage':3,'criticalDamage':4,'coverReminder':True,'dashBlocked':True,'chargeBonus':0})
        self.assertFalse(data['virus']['allowed']);self.assertFalse(data['virus']['apSpent'])
        self.assertEqual(data['regen']['wounds'],1);self.assertTrue(data['regen']['discardRemainingAttackDice'])
        self.assertEqual((data['amp']['apCost'],data['amp']['lethal'],data['amp']['hot']),(0,4,True))

    def test_carried_marker_update_is_available(self):
        self.assertIn('Update Carried Marker',APP);self.assertIn('marker.carrierId=',APP)
    def test_restless_tomb_event_count_unchanged(self):
        logic=APP.split('function strategyEventCount',1)[1].split('function threatLabel',1)[0]
        self.assertIn('restlessTombEnabled&&turningPoint>=2?Math.max(normalCount,1):normalCount',logic)
        self.assertNotIn('deadly',logic.lower())

    def test_deadly_encounters_does_not_use_event_deck_or_threat(self):
        self.assertNotIn('eventDeck',DE);self.assertNotIn('strategyEventCount',DE);self.assertNotIn('threat',DE.lower())

    def test_mission_05_awakenings_remain_separate(self):
        self.assertIn('awakenedRooms',APP);self.assertNotIn('awakenedRooms',DE)

    def test_npo_inventory_rosters_and_portraits_unchanged(self):
        self.assertNotIn('physicalQuantity',DE);self.assertNotIn('generateRoster',DE);self.assertNotIn('portrait',DE.lower())
        self.assertNotIn('obelisk',DE.lower())

    def test_help_is_pve_only_and_authoritative(self):
        help_section=APP.split('<summary>Deadly Encounters: Tomb Worlds</summary>',1)[1].split('</details>',1)[0]
        self.assertIn('PvE solo method',help_section);self.assertIn('official publication',help_section)
        self.assertNotIn('PvP',help_section)

    def test_accessible_d33_text_and_mobile_layout(self):
        self.assertIn('aria-label="D33 results',APP);self.assertIn('.d33-result',STYLES);self.assertIn('@media(max-width:390px)',STYLES)
        self.assertIn('feature-status',APP)

    def test_release_version_and_precache(self):
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.39'));self.assertIn('## v8.6.39',README)
        self.assertIn("const APP_VERSION = '8.6.39';",APP);self.assertIn("const APP_VERSION = '8.6.39';",WORKER);self.assertIn('V8.6.39',INDEX)
        self.assertIn('./deadly-encounters.js?v=${APP_VERSION}',WORKER)
        for asset in ['styles.css','mission-engine.js','persistence.js','deadly-encounters.js','app.js']:
            self.assertIn(f'{asset}?v=8.6.39',INDEX)


def _feature_test(feature_id, tokens):
    def test(self):
        feature=node(f"const d=require('./deadly-encounters.js');console.log(JSON.stringify(d.features.find(x=>x.id==='{feature_id}')))")
        self.assertIsNotNone(feature)
        combined=' '.join(str(feature.get(k,'')) for k in ['summary','timing','duration','automation','handler','cleanupTiming']).lower()
        for token in tokens:self.assertIn(token.lower(),combined)
    return test

FEATURE_EXPECTATIONS={
 'room-collapsed-ceiling':['move','cover'],'room-darkness':['visibility','6 inches'],'room-corrosive-fluid-leak':['activation','d3 damage'],
 'room-energy-rupture':['once-per-activation','d3 damage'],'room-airborne-virus':['apl','without spending ap'],'room-accelerated-decelerated-time':['activation restrictions','persist'],
 'room-crumbling-floor':['dash','charge'],'room-gravitic-anomaly':['move','melee damage'],
 'objective-quantum-shield':['defence-die reroll'],'objective-tesla-device':['d3 damage','movement action end'],'objective-teleportation-device':['guided','cancel'],
 'objective-control-node':['additional cp','once-per-turning-point'],'objective-temporal-sphere':['1ap','ready'],'objective-hyperphase-aura':['lethal 5+'],
 'objective-regeneration-sphere':['1 wound','once-per-operative-battle'],'objective-amplification-matrix':['0ap','lethal 4+','hot']
}
for feature_id,tokens in FEATURE_EXPECTATIONS.items():
    setattr(DeadlyEncounterIntegration,'test_feature_'+feature_id.replace('-','_'),_feature_test(feature_id,tokens))

if __name__=='__main__':unittest.main()
