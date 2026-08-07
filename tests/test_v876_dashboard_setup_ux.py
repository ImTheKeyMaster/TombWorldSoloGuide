from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
ONLINE = (ROOT / 'dashboard/controller/dashboard-online.js').read_text()


class DashboardSetupUxTests(unittest.TestCase):
    def test_home_visibility_tracks_resumable_game_and_async_availability(self):
        self.assertIn('if(canContinue)requestDashboardFeature()', APP)
        self.assertIn('isDashboardFeatureEnabled()', APP)
        self.assertIn('isDashboardWebRtcSupported()', APP)
        self.assertIn('subscribeAvailability(updateAvailability)', APP)
        self.assertIn('updateAvailability(await feature.requestDashboardAvailability', APP)
        self.assertIn("if($('#setupDashboardBtn')!==setupDashboardBtn)return", APP)
        self.assertIn('setupDashboardBtn.hidden=!available', APP)
        self.assertIn("$('#newGameBtn').onclick=()=>{stopDashboardAvailabilitySubscription()", APP)
        self.assertIn("if(savedGame){stopDashboardAvailabilitySubscription()", APP)
        self.assertIn("window.addEventListener('online', recheckRequestedAvailability)", ONLINE)
        self.assertIn("window.addEventListener('offline', recheckRequestedAvailability)", ONLINE)
        self.assertIn('lastAvailability = false', ONLINE)

    def test_pairing_opens_before_offer_and_ice_work(self):
        start = APP.index('async function openDashboardPairing')
        end = APP.index('async function addDashboardGameMenuSection', start)
        pairing = APP[start:end]
        self.assertLess(pairing.index("showModal('Setup Companion Dashboard',dashboardPairingPreparing()"),
                        pairing.index('await requestDashboardFeature()'))
        self.assertIn('Preparing secure dashboard link...', APP)
        self.assertLess(pairing.index("showModal('Setup Companion Dashboard',dashboardPairingPreparing()"),
                        pairing.index('createDashboardOffer('))
        self.assertIn('pairing-progress', CSS)
        self.assertIn('@media(prefers-reduced-motion:reduce)', CSS)

    def test_complete_url_is_shared_by_all_pairing_actions(self):
        self.assertIn('new URL("dashboard/",document.baseURI)', APP)
        self.assertIn('dashboardUrl.hash=`offer=${offer.encodedOffer}`', APP)
        self.assertIn("renderQrCode($('#dashboardOfferQr'),dashboardUrl.href", APP)
        self.assertIn("$('#dashboardUrl').value=dashboardUrl.href", APP)
        self.assertIn('navigator.clipboard.writeText(dashboardUrl.href)', APP)
        self.assertIn("navigator.share({title:'Tomb World Companion Dashboard',url:dashboardUrl.href})", APP)
        self.assertIn("$('#openDashboardUrl').href=dashboardUrl.href", APP)
        self.assertIn('target="_blank" rel="noopener noreferrer"', APP)

    def test_instructions_and_response_controls_remain_available(self):
        for text in ['scan the QR code below OR open the provided URL',
                     'generate a response QR code', 'Return to this device',
                     'Scan Dashboard Response', 'Paste Response',
                     'Waiting for dashboard device...', 'Dashboard Connected']:
            self.assertIn(text, APP)

    def test_menu_uses_same_pairing_routine(self):
        self.assertIn("$('#menuSetupDashboard').onclick=()=>openDashboardPairing(attempted)", APP)
        self.assertIn("${attempted?'Reestablish Pairing':'Setup Dashboard'}", APP)

    def test_failures_stay_in_modal_and_retry_cleans_up(self):
        self.assertIn('Dashboard Link Could Not Be Created', APP)
        self.assertIn('Dashboard setup requires an internet connection.', APP)
        self.assertIn('Unable to establish the WebRTC pairing offer.', APP)
        self.assertIn('await controller.disconnect()', APP)
        self.assertIn("$('#retryDashboardPairing').onclick=()=>", APP)
        self.assertNotIn("catch(error){dashboardPairingOpen=false;showToast", APP)

    def test_closing_during_async_setup_cannot_reopen_the_modal(self):
        self.assertIn('const generation=++dashboardPairingGeneration', APP)
        self.assertIn('const isCurrent=()=>dashboardPairingOpen&&generation===dashboardPairingGeneration', APP)
        self.assertIn('dashboardPairingGeneration+=1', APP)
        self.assertGreaterEqual(APP.count('if(!isCurrent())return;'), 6)


if __name__ == '__main__':
    unittest.main()
