from pathlib import Path
import json
import subprocess
import textwrap
import unittest

ROOT = Path(__file__).parents[1]


def node(script):
    result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


class LiveDashboardTests(unittest.TestCase):
    def test_meaningful_changes_and_revision_only_silence(self):
        script = textwrap.dedent("""
          import { detectDashboardChanges } from './dashboard/change-detector.js';
          const base={battle:{turningPoint:1,result:null},threat:{level:1,grade:1},readiness:{playerReady:2,npoReady:2},mission:{progress:0,objectives:[]},currentActivation:null,activeEvents:[],playerOperatives:[{id:'p',name:'Scout',wounds:8,status:'ready'}],npoOperatives:[]};
          const revision={...base,revision:2,updatedAt:9};
          const changed={...revision,battle:{turningPoint:2,result:'Victory'},threat:{level:2,grade:2},mission:{progress:1,objectives:[]},playerOperatives:[{id:'p',name:'Scout',wounds:0,status:'incapacitated'}],activeEvents:[{id:'e',title:'Awakening'}]};
          console.log(JSON.stringify({quiet:detectDashboardChanges(base,revision),types:detectDashboardChanges(base,changed).map(x=>x.type)}));
        """)
        result = node(script)
        self.assertEqual(result['quiet'], [])
        for kind in ['turningPoint','threat','grade','mission','wounds','incapacitated','eventAdded','battleComplete']:
            self.assertIn(kind, result['types'])

    def test_event_removal_and_latency_states(self):
        script = textwrap.dedent("""
          import { detectDashboardChanges } from './dashboard/change-detector.js';
          import { addLatencySample, averageLatency, linkState } from './dashboard/link-telemetry.js';
          const snapshot={battle:{turningPoint:1,result:null},threat:{level:1,grade:1},readiness:{playerReady:1,npoReady:1},mission:{progress:0,objectives:[]},currentActivation:null,playerOperatives:[],npoOperatives:[]};
          const a={...snapshot,activeEvents:[{id:'x',title:'Event'}]}, b={...snapshot,activeEvents:[]};
          const samples=addLatencySample(addLatencySample([],100,140),200,260);
          console.log(JSON.stringify({types:detectDashboardChanges(a,b).map(x=>x.type),average:averageLatency(samples),empty:averageLatency([]),live:linkState(1000,2000),degraded:linkState(1000,14000),interrupted:linkState(1000,32000)}));
        """)
        result = node(script)
        self.assertIn('eventRemoved', result['types'])
        self.assertEqual(result['average'], 50)
        self.assertIsNone(result['empty'])
        self.assertEqual([result['live'],result['degraded'],result['interrupted']], ['LIVE','LINK DEGRADED','LINK INTERRUPTED'])

    def test_safe_reduced_motion_and_no_gameplay_or_save_change(self):
        dashboard = (ROOT/'dashboard/dashboard.js').read_text()
        css = (ROOT/'dashboard/dashboard.css').read_text()
        controller = (ROOT/'dashboard/controller/dashboard-controller.js').read_text()
        self.assertNotIn('innerHTML', dashboard)
        self.assertIn('textContent', dashboard)
        self.assertIn("matchMedia('(prefers-reduced-motion: reduce)')", dashboard)
        self.assertIn('@media(prefers-reduced-motion:reduce)', css)
        self.assertIn('sentAt: Date.now()', controller)
        self.assertIn('const SAVE_VERSION = 3;', (ROOT/'persistence.js').read_text())
        self.assertNotIn('dashboard/change-detector', (ROOT/'app.js').read_text())

    def test_authored_feed_is_bounded_and_result_is_preserved(self):
        dashboard = (ROOT/'dashboard/dashboard.js').read_text()
        templates = (ROOT/'dashboard/data/cogitator-templates.js').read_text()
        self.assertIn('cogitatorFeed.splice(10)', dashboard)
        self.assertIn('previousSnapshot?.battle.result', dashboard)
        self.assertIn('Battle result confirmed:', templates)
        self.assertNotIn('fetch(', templates)
