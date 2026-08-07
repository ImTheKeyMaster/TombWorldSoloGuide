from pathlib import Path
import unittest
ROOT=Path(__file__).parents[1]
APP=(ROOT/'app.js').read_text(); CONFIG=(ROOT/'dashboard/shared/dashboard-config.js').read_text(); CODEC=(ROOT/'dashboard/shared/pairing-codec.js').read_text(); CONTROLLER=(ROOT/'dashboard/controller/dashboard-controller.js').read_text(); DASH=(ROOT/'dashboard/dashboard.js').read_text(); WORKER=(ROOT/'service-worker.js').read_text(); PERSIST=(ROOT/'persistence.js').read_text()
class DashboardPairingTests(unittest.TestCase):
 def test_visibility_and_lazy_loading(self):
  self.assertIn('id="setupDashboardBtn" hidden',APP); self.assertIn('canContinue&&feature.isDashboardFeatureEnabled()',APP); self.assertIn('feature.isDashboardWebRtcSupported()',APP); self.assertIn('await feature.requestDashboardAvailability',APP); self.assertIn("await import('./dashboard/controller/dashboard-controller.js')",APP)
 def test_config_is_stun_only(self):
  self.assertIn('stun:stun.cloudflare.com:3478',CONFIG); self.assertIn('stun:stun.cloudflare.com:53',CONFIG); self.assertNotIn('turn:',CONFIG.lower()); self.assertNotIn('credential',CONFIG.lower())
 def test_payload_validation(self):
  for value in ['protocolVersion','expectedType','expectedNonce','expiresAt','expectedSdpType','maximumPayloadSize']: self.assertIn(value,CODEC)
 def test_fragment_and_subpath(self):
  self.assertIn('location.hash',CODEC); self.assertIn('history.replaceState',CODEC); self.assertIn('new URL("dashboard/",document.baseURI)',APP); self.assertNotIn('searchParams',CODEC)
 def test_reliable_channel_and_cleanup(self):
  self.assertIn("createDataChannel('tomb-world-dashboard', { ordered: true })",CONTROLLER); self.assertNotIn('maxRetransmits',CONTROLLER); self.assertNotIn('maxPacketLifeTime',CONTROLLER); self.assertIn('channel?.close()',CONTROLLER); self.assertIn('peer?.close()',CONTROLLER); self.assertIn('stream.getTracks().forEach(track => track.stop())',(ROOT/'dashboard/shared/qr-utils.js').read_text())
 def test_handshake_has_no_gameplay_data(self):
  for message in ['DASHBOARD_READY','HELLO','HELLO_ACK']: self.assertIn(message,CONTROLLER+DASH)
  self.assertNotIn('SNAPSHOT)',CONTROLLER+DASH); self.assertNotIn('save()',CONTROLLER)
 def test_pairing_pages_network_only_and_save_unchanged(self):
  self.assertIn("fetch(request, {cache: 'no-store'})",WORKER); self.assertIn('const SAVE_VERSION = 3;',PERSIST)
if __name__=='__main__': unittest.main()
