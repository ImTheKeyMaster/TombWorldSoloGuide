import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


def run_node(script):
    return subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)


class MasterAudioRecoveryTests(unittest.TestCase):
    def test_release_and_parallel_unlock_contract(self):
        self.assertEqual((8, 6, 91), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        master = APP[APP.index("async function applySelectedAudioFromGesture") : APP.index("function syncNarrationControls")]
        narration_call = master.index("TombWorldNarration.unlock({force:true})")
        ambient_call = master.index("TombWorldAmbient.unlock()")
        wait = master.index("await Promise.allSettled")
        self.assertLess(narration_call, wait)
        self.assertLess(ambient_call, wait)
        self.assertIn("TombWorldNarration.isPlaybackEnabled()", master)
        self.assertIn("shouldAmbientBeActive()", master)

    def test_category_unlocks_and_failed_recovery_are_coordinated_once(self):
        coordinator = APP[APP.index("async function applySelectedAudioFromGesture") : APP.index("function syncNarrationControls")]
        self.assertIn("if(TombWorldNarration.isPlaybackEnabled())attempts.push(TombWorldNarration.unlock({force:true}))", coordinator)
        self.assertIn("if(shouldAmbientBeActive())attempts.push(TombWorldAmbient.unlock())", coordinator)
        self.assertIn("await Promise.allSettled(attempts)", coordinator)
        self.assertIn("if(recovered)removeAudioGestureRecovery()", coordinator)
        self.assertIn("else if(attempts.length)armAudioGestureRecovery()", coordinator)
        self.assertEqual(1, APP.count("document.addEventListener('click',audioRecoveryHandler,true)"))
        self.assertIn("document.removeEventListener('click',audioRecoveryHandler,true)", APP)

    def test_visibility_recovery_is_guarded_and_listener_is_unique(self):
        self.assertIn("document?.visibilityState !== 'visible'", AMBIENT)
        self.assertIn("recoveryRequired = true", AMBIENT)
        self.assertIn("tombworldaudiorecoveryrequired", AMBIENT)
        self.assertNotIn("addEventListener('click'", AMBIENT)

    def test_fallback_gesture_does_no_work_when_ambient_is_not_active(self):
        self.assertIn("if (activeBattle && masterEnabled()", AMBIENT)


if __name__ == "__main__":
    unittest.main()
