/* Tomb World local QR fallback adapter, Apache-2.0. The decoder hook is kept local so camera capture never uses a CDN. */
(function (global) {
  global.TombWorldQrDecoder = global.TombWorldQrDecoder || {
    supported: false,
    decode(imageData) {
      /* Native BarcodeDetector is preferred. Manual paste remains available on browsers without a native decoder. */
      void imageData;
      return null;
    }
  };
})(globalThis);
