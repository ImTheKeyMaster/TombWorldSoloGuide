# Optional companion dashboard

The dashboard is an optional, read-only companion display hosted alongside the main application by GitHub Pages. Version 8.7.1 pairs the game controller and dashboard directly with WebRTC. Offer and answer signaling is exchanged manually through QR codes, URL fragments, or copy/paste; there is no application backend and pairing fragments are removed after consumption.

All dashboard-specific code, styles, assets, protocol definitions, vendored QR files, and documentation are isolated under `dashboard/`. `DASHBOARD_FEATURE_ENABLED` and the STUN-only ICE configuration live in `shared/dashboard-config.js`. STUN is contacted only after the user selects Setup Dashboard. No gameplay save or snapshot is sent by the v8.7.1 handshake.
