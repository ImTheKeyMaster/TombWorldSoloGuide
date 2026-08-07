from pathlib import Path
import subprocess
import base64
import textwrap
import unittest

ROOT = Path(__file__).parents[1]
CONTROLLER = (ROOT / "dashboard/controller/dashboard-controller.js").read_text()
DASHBOARD = (ROOT / "dashboard/dashboard.js").read_text()
APP = (ROOT / "app.js").read_text()
CONFIG = (ROOT / "dashboard/shared/dashboard-config.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class DashboardIceTests(unittest.TestCase):
    def run_node(self, source):
        result = subprocess.run(
            ["node", "--input-type=module", "-e", source.replace("HELPER_URL", "data:text/javascript;base64," + base64.b64encode((ROOT / "dashboard/shared/webrtc-ice.js").read_bytes()).decode())],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_candidate_collector_completion_paths_and_safe_diagnostics(self):
        self.run_node(textwrap.dedent("""
            import assert from 'node:assert/strict';
            import { collectIceCandidates, NoIceCandidatesError } from 'HELPER_URL';
            class Peer extends EventTarget { constructor(){ super(); this.iceGatheringState='gathering'; } emit(type, values={}) { const event=new Event(type); Object.assign(event, values); this.dispatchEvent(event); } }
            const rtc = (value, type='host') => ({ toJSON:()=>({candidate:`candidate:${value} 1 udp 1 192.0.2.${value} 9 typ ${type}`,sdpMid:'0',sdpMLineIndex:0}) });

            let peer=new Peer(), promise=collectIceCandidates(peer,{quietPeriodMs:15,maximumWaitMs:100});
            peer.emit('icecandidate',{candidate:rtc(1)}); let result=await promise;
            assert.equal(result.candidates.length,1); assert.equal(result.completed,false); assert.equal(result.gatheringState,'gathering');

            peer=new Peer(); promise=collectIceCandidates(peer,{quietPeriodMs:50,maximumWaitMs:100});
            peer.emit('icecandidate',{candidate:rtc(1)}); peer.emit('icecandidate',{candidate:rtc(2,'srflx')}); peer.emit('icecandidate',{candidate:null}); result=await promise;
            assert.equal(result.candidates.length,2); assert.equal(result.completed,true); assert.deepEqual(result.diagnostics.candidateTypes,['host','srflx']);

            peer=new Peer(); promise=collectIceCandidates(peer,{quietPeriodMs:50,maximumWaitMs:100}); peer.iceGatheringState='complete'; peer.emit('icegatheringstatechange');
            await assert.rejects(promise, NoIceCandidatesError);

            peer=new Peer(); promise=collectIceCandidates(peer,{quietPeriodMs:100,maximumWaitMs:15}); peer.emit('icecandidate',{candidate:rtc(3)}); result=await promise;
            assert.equal(result.candidates.length,1); assert.equal(result.completed,false);

            peer=new Peer(); promise=collectIceCandidates(peer,{quietPeriodMs:100,maximumWaitMs:15});
            peer.emit('icecandidateerror',{errorCode:701,errorText:'failed at 192.168.1.2',url:'stun:stun.cloudflare.com:3478'});
            const error=await promise.catch(value=>value); assert.equal(error.name,'NoIceCandidatesError'); assert.equal(error.diagnostics.stunErrors[0].server,'stun.cloudflare.com');
            assert.equal(JSON.stringify(error.diagnostics).includes('192.168.1.2'),false);
        """))

    def test_remote_candidate_deduplication(self):
        self.run_node(textwrap.dedent("""
            import assert from 'node:assert/strict';
            import { addRemoteIceCandidates } from 'HELPER_URL';
            const candidate={candidate:'candidate:1 1 udp 1 192.0.2.1 9 typ host',sdpMid:'0',sdpMLineIndex:0};
            const peer={added:[],async addIceCandidate(value){this.added.push(value)}};
            await addRemoteIceCandidates(peer,[candidate,candidate],'v=0'); assert.equal(peer.added.length,1);
            peer.added=[]; await addRemoteIceCandidates(peer,[candidate],`v=0\r\na=${candidate.candidate}\r\n`); assert.equal(peer.added.length,0);
        """))

    def test_candidate_payload_validation(self):
        codec = (ROOT / "dashboard/shared/pairing-codec.js").read_text()
        for value in ["maximumCandidates = 32", "maximumCandidateLength = 2048", "Array.isArray(candidates)", "sdpMid.length > 64", "sdpMLineIndex < 0", "validateCandidates(data.candidates)"]:
            self.assertIn(value, codec)

    def test_both_payloads_and_receivers_use_explicit_candidates(self):
        self.assertIn("candidates: gathered.candidates", CONTROLLER)
        self.assertIn("candidates: gathered.candidates", DASHBOARD)
        self.assertIn("addRemoteIceCandidates(peer, answer.candidates, answer.sdp)", CONTROLLER)
        self.assertIn("addRemoteIceCandidates(peer, offer.candidates, offer.sdp)", DASHBOARD)
        self.assertNotIn("function waitForIce", CONTROLLER + DASHBOARD)

    def test_retry_cleanup_progress_and_existing_pairing_controls(self):
        self.assertIn("iceAbortController?.abort()", CONTROLLER)
        self.assertIn("pairingDiagnostics = null", CONTROLLER)
        self.assertIn("generation += 1", CONTROLLER)
        for value in ["Creating WebRTC session...", "Discovering network route...", "Generating pairing code...", "Technical Details"]:
            self.assertIn(value, APP + CONTROLLER)
        for value in ["renderQrCode($('#dashboardOfferQr'),dashboardUrl.href", "navigator.clipboard.writeText(dashboardUrl.href)", "navigator.share", "Scan Dashboard Response"]:
            self.assertIn(value, APP)

    def test_stun_only_read_only_and_save_version_unchanged(self):
        self.assertIn("stun:stun.cloudflare.com:3478", CONFIG)
        self.assertIn("stun:stun.l.google.com:19302", CONFIG)
        self.assertNotIn("turn:", CONFIG.lower())
        self.assertNotIn("credential", CONFIG.lower())
        self.assertNotIn("save()", CONTROLLER)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
