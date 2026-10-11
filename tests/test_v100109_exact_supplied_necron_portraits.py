from hashlib import sha256
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "NecronActivation"

EXPECTED_SHA256 = {
    "canoptek-macrocyte-accelerator.webp": "efd779a89da9f52d2f5cd9701d3eeb9660141888a1156c0358eb216abc6aa701",
    "canoptek-macrocyte-reanimator.webp": "307a8b44ded81a5766dfb7011646519d5cdd1a4b912ed39d07327c4e6da1916c",
    "canoptek-macrocyte-warrior-1.webp": "c5226fd44e95ffa5d65235cab8a9022b7fed4930ab30b1d25e544b883673ad72",
    "canoptek-macrocyte-warrior-2.webp": "50c509ba389b472c678e363e570d52af0e34cfa333770f62283e1c6a370fd3dd",
    "canoptek-macrocyte-warrior-3.webp": "373c9c06e43cd8ccf3a48747f7983bc651ac33837bd1a66f9d4603de3d908cea",
    "canoptek-scarab-swarm.webp": "b1c12e60d7ac5cccbf407f158c18642d63edfe63c2a283cc6c8ec10a2e7b11d3",
    "canoptek-tomb-crawler-1.webp": "47d4d993033c668e3af607f2eca0b4d777648ea112f2483cf58dd10533c3086d",
    "canoptek-tomb-crawler-2.webp": "476c4a12acf8e9b32f9a5783376fdacd318e13ff6729d9bcddfeb4eb0ec2a078",
    "geomancer.webp": "79c6661e2b26315a4feb18ff080bc5fb85f7f29120c9725565f4563c70e71377",
    "necron-warrior-gauss-flayer.webp": "6590049c6374efc14d58e4225e6de40d334cd11839020d859780966e76d03e6a",
    "necron-warrior-gauss-reaper.webp": "e682e3ade82bee37b0009f845c30b38eb28da1cc92fb90de9500dab67a8192c1",
}


def test_release_is_v100110_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 110)


def test_exact_supplied_green_portrait_assets_are_committed():
    for filename, expected in EXPECTED_SHA256.items():
        data = (ASSET_ROOT / filename).read_bytes()
        assert sha256(data).hexdigest() == expected, filename


def test_necron_portraits_are_still_direct_rendered_without_runtime_recoloring():
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    start = app.index("function experimentalNecronPortraitSvg")
    end = app.index("function experimentalNecronPortraitMarkup", start)
    source = app[start:end]

    assert '<image href="' in source
    assert "<filter" not in source
    assert "feColorMatrix" not in source
    assert "feComponentTransfer" not in source
    assert "feConvolveMatrix" not in source


def test_supplied_necron_webps_have_384_square_pixels_and_alpha():
    for filename in EXPECTED_SHA256:
        data = (ASSET_ROOT / filename).read_bytes()
        assert data[0:4] == b"RIFF" and data[8:16] == b"WEBPVP8X", filename
        assert data[20] & 0x10, filename  # VP8X alpha flag
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        assert (width, height) == (384, 384), filename


def test_necron_portrait_urls_are_versioned_in_renderer_and_precache():
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert 'const versionedHref=`${href}?v=${APP_VERSION}`;' in app
    assert 'escapeHtml(versionedHref)' in app
    for filename in EXPECTED_SHA256:
        path = f'./Assets/Images/TombUI/NecronActivation/{filename}?v=${{APP_VERSION}}'
        assert path in worker, filename
