from pathlib import Path
import subprocess
import textwrap
import unittest

ROOT = Path(__file__).parents[1]
QR_UTILS = (ROOT / 'dashboard/shared/qr-utils.js').read_text()
ADAPTER = (ROOT / 'dashboard/vendor/qr-decoder.js').read_text()
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


class IphoneDashboardQrTests(unittest.TestCase):
    def test_vendored_jsqr_and_adapter(self):
        library = ROOT / 'dashboard/vendor/jsQR.js'
        self.assertGreater(library.stat().st_size, 200_000)
        self.assertTrue((ROOT / 'dashboard/vendor/jsQR-LICENSE.txt').is_file())
        self.assertIn('webpackUniversalModuleDefinition', library.read_text())
        self.assertIn("supported: typeof global.jsQR === 'function'", ADAPTER)
        script = textwrap.dedent(f"""
            const assert=require('node:assert/strict'),vm=require('node:vm');
            const context={{globalThis:null,jsQR:(data,width,height)=>data[0]===7?{{data:`${{width}}x${{height}}`}}:null}};
            context.globalThis=context;vm.runInNewContext({ADAPTER!r},context);
            assert.equal(context.TombWorldQrDecoder.supported,true);
            assert.equal(context.TombWorldQrDecoder.decode({{data:[7],width:12,height:34}}),'12x34');
            assert.equal(context.TombWorldQrDecoder.decode({{data:[0],width:1,height:1}}),null);
        """)
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_camera_is_requested_before_decoder_initialization(self):
        camera = QR_UTILS.index('navigator.mediaDevices.getUserMedia')
        detector = QR_UTILS.index('await nativeQrDetector()', camera)
        fallback = QR_UTILS.index('await ensureFallbackDecoder()', camera)
        self.assertLess(camera, detector)
        self.assertLess(camera, fallback)
        self.assertIn("facingMode: { ideal: 'environment' }", QR_UTILS)
        self.assertIn('audio: false', QR_UTILS)

    def test_iphone_fallback_video_and_throttled_frames(self):
        self.assertIn("typeof globalThis.BarcodeDetector !== 'function'", QR_UTILS)
        self.assertIn("formats.includes('qr_code')", QR_UTILS)
        self.assertIn("new URL('../vendor/jsQR.js', import.meta.url)", QR_UTILS)
        self.assertIn("new URL('../vendor/qr-decoder.js', import.meta.url)", QR_UTILS)
        for value in ["setAttribute('playsinline'", "setAttribute('autoplay'", "setAttribute('muted'",
                      'video.playsInline = true', 'video.autoplay = true', 'video.muted = true']:
            self.assertIn(value, QR_UTILS)
        self.assertIn('setTimeout(decode, 80)', QR_UTILS)
        self.assertNotIn('https://', QR_UTILS + ADAPTER)

    def test_native_failure_paths_fall_back(self):
        self.assertIn('BarcodeDetector.getSupportedFormats()', QR_UTILS)
        self.assertIn("return new BarcodeDetector({ formats: ['qr_code'] })", QR_UTILS)
        self.assertIn('if (++detectorFailures >= 3)', QR_UTILS)
        self.assertIn('fallback = await ensureFallbackDecoder()', QR_UTILS)

    def test_validation_cleanup_and_visible_scanner(self):
        for text in ['Point this device at the response QR code shown on the Dashboard.',
                     'Not a Tomb World Dashboard response.', 'Scan from Photo',
                     'Camera Access Required', 'Camera Unavailable',
                     'Live QR scanning is not supported by this browser.',
                     'Try Camera Again', 'Paste Response']:
            self.assertIn(text, APP)
        self.assertIn('if (await onResult(value)) { stop(); return; }', QR_UTILS)
        self.assertIn('stream.getTracks().forEach(track => track.stop())', QR_UTILS)
        self.assertIn('video.srcObject = null', QR_UTILS)
        self.assertIn('cancelAnimationFrame(frameRequest)', QR_UTILS)
        self.assertIn('input.remove()', QR_UTILS)
        self.assertIn('pairing-camera-target', APP + CSS)
        self.assertGreaterEqual(APP.count('stopPairingCamera()'), 8)

    def test_photo_fallback_is_local_and_save_version_is_unchanged(self):
        self.assertIn("input.accept = 'image/*'", QR_UTILS)
        self.assertIn("input.capture = 'environment'", QR_UTILS)
        self.assertIn('URL.createObjectURL(file)', QR_UTILS)
        self.assertIn('URL.revokeObjectURL(url)', QR_UTILS)
        self.assertIn('decoder.decode(imageDataFrom(image', QR_UTILS)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
