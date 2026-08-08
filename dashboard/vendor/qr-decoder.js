/* Local adapter for the vendored jsQR browser build. */
(function (global) {
  global.TombWorldQrDecoder = {
    supported: typeof global.jsQR === 'function',
    decode(imageData) {
      if (typeof global.jsQR !== 'function') return null;
      const result = global.jsQR(imageData.data, imageData.width, imageData.height);
      return result?.data || null;
    }
  };
})(globalThis);
