# Optional companion dashboard

The dashboard is an optional, read-only companion display hosted alongside the main application by GitHub Pages. There is no application backend.

A future release will pair the game controller and dashboard with WebRTC. Signaling will be exchanged manually through QR codes or URLs; this foundation neither creates a WebRTC connection nor contacts a STUN server. Dashboard data will remain read-only and will not provide gameplay commands or writable actions.

All dashboard-specific code, styles, assets, protocol definitions, vendor files, and documentation are intentionally isolated under `dashboard/`. Removing the feature should require deleting this directory and the small blocks in root files marked `DASHBOARD INTEGRATION START` and `DASHBOARD INTEGRATION END`.

`DASHBOARD_FEATURE_ENABLED` in `shared/dashboard-config.js` is the central feature switch. The main app may lazy-load the controller only after a future user action requests it, and availability must first be confirmed with the network-only online probe.
