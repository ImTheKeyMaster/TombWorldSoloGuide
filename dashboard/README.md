# Optional companion dashboard

The dashboard is an optional, read-only companion display hosted alongside the main application by GitHub Pages. It has no backend and stores no game state remotely. The controller sends a minimized snapshot directly over an encrypted WebRTC data channel; the dashboard cannot send gameplay commands.

## Pairing and availability

Setup is offered only while an active game can be resumed and a network-only probe succeeds. Setup never comes from the PWA cache. Selecting **Setup Dashboard** starts STUN-only connection discovery; merely loading or resuming the game does not create a peer connection. Camera permission is requested only after **Scan Dashboard Response** is selected, and copy/paste remains available.

Pairing is a two-step QR exchange: open the controller's offer on the dashboard, then scan the dashboard's response on the controller. Pairing is one-time for each uninterrupted browser session and snapshots update automatically afterward. A same-network connection is recommended, but connection is not guaranteed on guest, client-isolated, or restrictive Wi-Fi networks. There is no TURN relay, polling, SSE, WebSocket service, Firebase, Supabase, or GitHub API signaling.

Reloading either page destroys its WebRTC objects. The dashboard retains its last valid snapshot in `sessionStorage`, labels it **COGITATOR LINK LOST**, and does not pretend it is live. Reestablish pairing from Game Menu after both devices are online. Raw SDP and camera data are never placed in `localStorage`; URL fragments are removed from browser history after consumption.

## Privacy, security, and compatibility

Only the current read-only dashboard projection crosses the peer channel. Pairing protocol/type, nonce, expiry, SDP type, message type and size, snapshot schema, and revision are validated. Unexpected dashboard messages are ignored, repeated violations close the channel, incoming code is never evaluated, and incoming text is rendered with `textContent`. No repository credentials or tokens exist in the feature.

Current Safari, Chrome, or another browser with WebRTC, Web Crypto, and (for scanning) camera support is required. The controller remains usable without camera access. The transport publishes through an internal collection of active channels so future multiple-viewer support will not require coupling gameplay to one channel; this release intentionally exposes only one-dashboard setup.

## Removal procedure

The dashboard has no gameplay dependency. To remove it:

1. Delete `dashboard/`.
2. Remove every clearly marked `DASHBOARD INTEGRATION` block.
3. Remove the dashboard-specific service-worker network-only exclusions.
4. Remove dashboard tests.
5. Remove dashboard feature documentation from the root README.

Setting `DASHBOARD_FEATURE_ENABLED = false` disables all entry points while the game, saving, and offline app shell continue normally.
