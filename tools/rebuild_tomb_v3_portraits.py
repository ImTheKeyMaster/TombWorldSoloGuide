#!/usr/bin/env python3
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "Assets/Images/TombUI/v3/source/portraits-corrupt.webp"
dst = ROOT / "Assets/Images/TombUI/v3/portraits.webp"

raw = src.read_bytes()
encoded = base64.b64encode(raw).decode("ascii")

# The connector staging blob contains one duplicated 10,000-character
# base64 segment at [20000:30000]. Remove that duplicate and decode.
fixed = encoded[:20000] + encoded[30000:]
data = base64.b64decode(fixed, validate=True)

expected_len = 27970
expected_blob_sha = "5c9498b349154c23fe0e1246316811c7e6dbbb34"
actual_blob_sha = hashlib.sha1(
    b"blob " + str(len(data)).encode("ascii") + b"\0" + data
).hexdigest()

if len(data) != expected_len:
    raise SystemExit(f"Unexpected portrait sprite length: {len(data)}")
if actual_blob_sha != expected_blob_sha:
    raise SystemExit(f"Unexpected portrait sprite git SHA: {actual_blob_sha}")

dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(data)
src.unlink()
print(f"Wrote {dst.relative_to(ROOT)} ({len(data)} bytes)")
