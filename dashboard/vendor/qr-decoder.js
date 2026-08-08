/* Local adapter for the vendored jsQR browser build. */
(function (global) {
  global.TombWorldQrDecoder = {
    supported: true,
    decode(imageData) {
      if (typeof global.jsQR !== 'function') return null;
      try {
        const result = global.jsQR(imageData.data, imageData.width, imageData.height);
        return result?.data || null;
      } catch { return null; }
    }
  };
})(globalThis);
