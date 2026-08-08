# Vendored QR dependencies

- `qrcode-generator.js`: local QR encoder used for Dashboard pairing. MIT; see `LICENSE-qrcode-generator.txt`.
- `jsQR.js`: jsQR 1.4.0 browser production build from cozmo/jsQR, manually vendored from the upstream GitHub repository. Apache-2.0; see `jsQR-LICENSE.txt`.
- `qr-decoder.js`: local adapter that exposes the vendored jsQR build as `TombWorldQrDecoder`. QR processing remains on the device and requires no CDN.
