#!/usr/bin/env python3
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class PersistentNpoReadinessV9250Tests(unittest.TestCase):
    def source(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_scout_room_threat_drop_preserves_mixed_persistent_states(self):
        set_threat = "function setThreat(amount,reason){" + self.source(
            "function setThreat(amount,reason){", "function escapeHtml"
        )
        tracker_helpers = "function activeNpos(){" + self.source(
            "function activeNpos(){", "function livingPlayerOperativeCount"
        )
        script = f"""
const assert=require('assert').strict;
const state={{
  threat:3,npoActivated:1,activeNpoId:null,lastActivation:null,
  activationFinishedForTurningPoint:{{player:false,npo:false}},
  gradeMilestoneSequence:0,gradeMilestone:null,journal:[],
  roster:Array.from({{length:4}},(_,index)=>({{
    id:`room-1-${{index+1}}`,wounds:7,battlefieldState:'deployed',deployed:true,
    ready:true,dormant:false
  }}))
}};
const GRADE_CONFIG=[
  {{grade:0,name:'Dormant',minThreat:0,maxThreat:0}},
  {{grade:1,name:'Stirring',minThreat:1,maxThreat:5}},
  {{grade:2,name:'Awakened',minThreat:6,maxThreat:10}},
  {{grade:3,name:'Overrun',minThreat:11,maxThreat:15}}
];
function boundedInteger(value,min,max,fallback=min){{const number=Number(value);return Number.isFinite(number)?Math.min(max,Math.max(min,Math.trunc(number))):fallback;}}
function threatGrade(){{return GRADE_CONFIG.find(config=>state.threat>=config.minThreat&&state.threat<=config.maxThreat)?.grade??0;}}
function gradeConfig(grade){{return GRADE_CONFIG.find(config=>config.grade===Number(grade))||GRADE_CONFIG[0];}}
function threatLabel(){{return gradeConfig(threatGrade()).name;}}
function log(text){{state.journal.unshift({{time:'test',text}});state.journal=state.journal.slice(0,150);}}
{tracker_helpers}
{set_threat}

log('4 Necrons were generated for Eligible room 1. They are Ready immediately.');
state.roster[0].ready=false;
state.roster[0].wounds=0;
state.roster[0].deployed=false;
state.roster[0].battlefieldState='out-of-action';
setThreat(-3,'Scout Room');
assert.equal(state.threat,0);
assert.deepEqual(state.roster.slice(1,4).map(npo=>[npo.ready,npo.dormant]),[
  [true,false],[true,false],[true,false]
]);

for(let index=0;index<2;index++)state.roster.push({{
  id:`room-4-${{index+1}}`,wounds:7,battlefieldState:'deployed',deployed:true,
  ready:false,dormant:true
}});
log('2 Necrons were generated for Eligible room 4. Threat is 0, so they are Dormant.');

const statuses=trackerNpos().map(npo=>npoTrackerStatus(npo).status);
assert.equal(statuses.filter(status=>status==='READY').length,3);
assert.equal(statuses.filter(status=>status==='DORMANT').length,2);
assert.equal(statuses.filter(status=>status==='ELIMINATED').length,1);
assert.deepEqual(readyNpos().map(npo=>npo.id),['room-1-2','room-1-3','room-1-4']);
assert(state.journal.some(entry=>entry.text.includes('4 Necrons were generated')&&entry.text.includes('Ready immediately')));
assert(state.journal.some(entry=>entry.text==='Threat 3 → 0: Scout Room'));
assert(state.journal.some(entry=>entry.text.includes('2 Necrons were generated')&&entry.text.includes('Dormant')));
assert(!state.journal.some(entry=>entry.text.includes('Dormant NPOs became Ready')));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_all_ready_consumers_use_the_persistent_ready_filter(self):
        ready = self.source("function readyNpos()", "function trackerNpos()")
        self.assertIn("n.ready&&!n.dormant", ready)

        hud = self.source("function hud()", "function phaseTrack")
        self.assertIn("readyNpos().length", hud)

        selector = self.source("function showNpoSelection()", "function remainingPlayerOperatives")
        self.assertIn("const candidates=readyNpos()", selector)
        self.assertIn("sortedNposForDisplay(candidates)", selector)

        tracker = self.source("function activationTracker()", "function showPlayerOperativeStatus")
        self.assertIn("npoTrackerStatus(n)", tracker)

    def test_threat_and_ready_step_never_demote_a_ready_npo(self):
        threat = self.source("function setThreat(amount,reason)", "function escapeHtml")
        self.assertNotIn("npo.dormant=true", threat)
        self.assertNotIn("npo.ready=false", threat)

        ready_step = self.source("function processReadyStep()", "function applyMissionReadyHooks")
        self.assertIn("filter(npo=>!npo.dormant)", ready_step)
        self.assertNotIn("npo.dormant=", ready_step)

        awakening = self.source("async function performAwakenRoom(roomId)", "function continueAfterAwakenRoom")
        self.assertIn("ready:state.threat>0,dormant:state.threat===0", awakening)
        self.assertIn("They are Ready immediately", awakening)
        self.assertIn("they are Dormant", awakening)


if __name__ == "__main__":
    unittest.main()
